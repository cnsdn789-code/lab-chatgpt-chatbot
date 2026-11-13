
#!/usr/bin/env python3
"""
멀티턴 AI 챗봇 CLI
최근 10턴만 기억하는 Sliding Window Memory 적용
실행: python chat_cli.py
"""

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

try:
    from prompt_toolkit import prompt
    USE_PROMPT_TOOLKIT = True
except ImportError:
    USE_PROMPT_TOOLKIT = False


# 1. 초기 설정
load_dotenv()
client = OpenAI()

MODEL = "gpt-6-luna"
MAX_TURNS = 10  # 최근 10턴만 기억

SYSTEM = (
    "당신은 친절한 AI 어시스턴트입니다. "
    "모르면 '확인 필요'라고만 답하세요."
)

history = []
usage_log = []


def reset():
    """대화 기록 및 사용량 초기화."""
    history.clear()
    usage_log.clear()
    print("(대화 초기화)")


def read_input():
    """사용자 입력 받기."""
    if USE_PROMPT_TOOLKIT:
        return prompt("You: ").strip()

    return input("You: ").strip()


def chat(message: str, temperature: float = 0.3) -> str:
    """최근 10턴의 대화 기록을 활용해 AI 답변 생성."""

    user_message = {
        "role": "user",
        "content": message
    }

    # 이전 대화 최대 10턴 + 현재 질문
    messages = [
        {"role": "system", "content": SYSTEM},
        *history,
        user_message
    ]

    # LLM 호출
    resp = client.chat.completions.create(
        model=MODEL,
        reasoning_effort="none",
        temperature=temperature,
        messages=messages,
    )

    answer = resp.choices[0].message.content

    if not answer:
        raise ValueError("AI 답변이 비어 있습니다.")

    # 호출 성공 시 대화 저장
    history.append(user_message)
    history.append({
        "role": "assistant",
        "content": answer
    })

    # 최근 10턴(메시지 20개)만 유지
    if len(history) > MAX_TURNS * 2:
        del history[:-MAX_TURNS * 2]

    # 토큰 사용량 저장
    if resp.usage is not None:
        usage_log.append(resp.usage.total_tokens)

    return answer


def show_stats():
    """토큰 및 예상 비용 출력."""

    if not usage_log:
        print("(아직 사용 기록 없음)")
        return

    # 실습용 혼합 평균 단가
    PRICE = 0.30 / 1_000_000
    EXCHANGE_RATE = 1400

    total = sum(usage_log)
    per_turn = total / len(usage_log)

    cost_krw = total * PRICE * EXCHANGE_RATE

    print("\n[사용량 통계]")
    print(f"  총 대화 턴 수: {len(usage_log)}")
    print(f"  현재 기억 중인 턴 수: {len(history) // 2}/{MAX_TURNS}")
    print(f"  누적 토큰: {total:,}")
    print(f"  평균 턴당: {per_turn:.1f} tokens")
    print(f"  누적 예상 비용: {cost_krw:.4f}원")
    print(
        f"  10턴 단순 추정: "
        f"{per_turn * 10 * PRICE * EXCHANGE_RATE:.4f}원"
    )
    print("  ※ 혼합 평균 단가를 사용한 간이 추정치\n")


def show_history():
    """현재 기억 중인 대화 기록 조회."""

    if not history:
        print("(대화 기록이 없습니다.)")
        return

    print(f"\n========== 최근 {MAX_TURNS}턴 대화 기록 ==========")

    for i, message in enumerate(history, start=1):
        role = message["role"]
        content = message["content"]

        name = "나" if role == "user" else "AI"
        print(f"{i}. [{name}] {content}")

    print("====================================\n")


def save_history():
    """현재 기억 중인 대화를 TXT로 저장."""

    if not history:
        print("(저장할 대화가 없습니다.)")
        return

    save_dir = Path("chat_logs")
    save_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"chat_{now}.txt"

    lines = [
        "AI 챗봇 대화 기록",
        f"저장 일시: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"최근 {MAX_TURNS}턴",
        "=" * 40,
        ""
    ]

    for message in history:
        name = "나" if message["role"] == "user" else "AI"

        lines.append(f"[{name}]")
        lines.append(message["content"])
        lines.append("")

    file_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(f"(대화 저장 완료: {file_path.resolve()})")


def main():
    """메인 챗봇 실행."""

    print("=" * 60)
    print("멀티턴 AI 챗봇 CLI")
    print(f"최근 {MAX_TURNS}턴 기억 모드")
    print("=" * 60)
    print("명령어:")
    print("  /reset   - 대화 초기화")
    print("  /stats   - 토큰 및 비용 확인")
    print("  /history - 최근 대화 기록 확인")
    print("  /save    - 현재 대화 TXT 저장")
    print("  /quit    - 종료")
    print("=" * 60)

    if USE_PROMPT_TOOLKIT:
        print("(입력 편집 기능 활성화)")
    else:
        print("(기본 입력 모드)")

    print()
    reset()

    while True:
        try:
            user_input = read_input()

            if not user_input:
                continue

            if user_input == "/reset":
                reset()
                continue

            if user_input == "/stats":
                show_stats()
                continue

            if user_input == "/history":
                show_history()
                continue

            if user_input == "/save":
                save_history()
                continue

            if user_input == "/quit":
                print("(대화 종료)")
                break

            print("Bot: ", end="", flush=True)

            response = chat(user_input)

            print(response)
            print()

        except (KeyboardInterrupt, EOFError):
            print("\n(대화 종료)")
            break

        except Exception as e:
            print(f"\n오류 발생: {e}")
            print("(실패한 질문은 기록에 저장되지 않습니다.)")
            print()


if __name__ == "__main__":
    main()
