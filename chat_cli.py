#!/usr/bin/env python3
"""
멀티턴 AI 챗봇 CLI
현재 실행 중인 대화를 모두 기억합니다.

실행:
    python chat_cli.py
"""

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

try:
    from prompt_toolkit import prompt
    USE_PROMPT_TOOLKIT = True
except ImportError:
    USE_PROMPT_TOOLKIT = False


# 1. 초기 설정
load_dotenv()

MODEL = "gpt-6-luna"

SYSTEM = (
    "당신은 친절한 AI 어시스턴트입니다. "
    "모르면 '확인 필요'라고 답하세요."
)

llm = ChatOpenAI(
    model=MODEL,
    reasoning_effort="none",
    temperature=0.3,
)

# 프로그램 실행 중 대화를 모두 메모리에 보관합니다.
history = []
usage_log = []


def reset():
    """대화 기록 및 사용량 기록 초기화."""
    history.clear()
    usage_log.clear()
    print("(대화 초기화)")


def read_input():
    """사용자 입력 받기."""
    if USE_PROMPT_TOOLKIT:
        return prompt("You: ").strip()

    return input("You: ").strip()


def chat(message: str, temperature: float = 0.3) -> str:
    """이전 대화 전체를 포함해 AI 답변 생성."""

    user_message = {
        "role": "user",
        "content": message,
    }

    # system 메시지와 지금까지의 대화, 새 질문을 모델에 전달
    messages = [SystemMessage(content=SYSTEM)]

    for item in [*history, user_message]:
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        else:
            messages.append(AIMessage(content=item["content"]))

    # LangChain으로 모델 호출
    response = llm.bind(temperature=temperature).invoke(messages)
    answer = response.content

    if not answer or not answer.strip():
        raise ValueError("AI 답변이 비어 있습니다.")

    # 답변을 받은 경우에만 질문과 답을 대화 기록에 저장
    history.append(user_message)
    history.append({
        "role": "assistant",
        "content": answer,
    })

    # LangChain 응답에서 토큰 사용량 기록
    usage = response.usage_metadata or {}
    total_tokens = usage.get("total_tokens")

    if total_tokens is None:
        response_metadata = response.response_metadata or {}
        token_usage = response_metadata.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens")

    if total_tokens is not None:
        usage_log.append(total_tokens)

    return answer


def show_stats():
    """토큰 및 예상 비용 출력."""

    if not usage_log:
        print("(아직 사용 기록이 없습니다.)")
        return

    # 아래 단가는 실습용 간이 추정치입니다.
    price_per_million_tokens = 0.30
    exchange_rate = 1400

    total_tokens = sum(usage_log)
    average_tokens = total_tokens / len(usage_log)
    estimated_cost = (
        total_tokens
        * price_per_million_tokens
        / 1_000_000
        * exchange_rate
    )

    print("\n[사용량 통계]")
    print(f"  성공한 대화 턴 수: {len(usage_log)}")
    print(f"  현재 대화 기록: {len(history) // 2}턴")
    print(f"  응답 사용량 합계: {total_tokens:,} tokens")
    print(f"  응답당 평균 사용량: {average_tokens:.1f} tokens")
    print(f"  누적 예상 비용: 약 {estimated_cost:.4f}원")
    print("  ※ 입력 토큰·모델별 요금이 반영되지 않은 간이 추정치입니다.\n")


def show_history():
    """현재 실행 중인 대화 전체 조회."""

    if not history:
        print("(대화 기록이 없습니다.)")
        return

    print("\n========== 전체 대화 기록 ==========")

    for index, message in enumerate(history, start=1):
        name = "나" if message["role"] == "user" else "AI"
        print(f"\n{index}. [{name}]")
        print(message["content"])

    print("\n====================================\n")


def save_history():
    """현재 실행 중인 대화 전체를 TXT 파일로 저장."""

    if not history:
        print("(저장할 대화가 없습니다.)")
        return

    save_dir = Path("chat_logs")
    save_dir.mkdir(parents=True, exist_ok=True)

    saved_at = datetime.now()
    file_path = save_dir / f"chat_{saved_at:%Y%m%d_%H%M%S}.txt"

    lines = [
        "AI 챗봇 대화 기록",
        f"저장 일시: {saved_at:%Y-%m-%d %H:%M:%S}",
        f"총 대화 턴: {len(history) // 2}",
        "=" * 40,
        "",
    ]

    for message in history:
        name = "나" if message["role"] == "user" else "AI"
        lines.append(f"[{name}]")
        lines.append(message["content"])
        lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"(대화 저장 완료: {file_path.resolve()})")


def show_help():
    """명령어 안내."""
    print("\n명령어:")
    print("  /reset   - 대화 기록과 사용량 초기화")
    print("  /stats   - 토큰 사용량과 예상 비용 확인")
    print("  /history - 현재 대화 기록 확인")
    print("  /save    - 현재 대화를 TXT 파일로 저장")
    print("  /help    - 명령어 안내")
    print("  /quit    - 종료\n")


def main():
    """메인 챗봇 실행."""

    print("=" * 60)
    print("멀티턴 AI 챗봇 CLI")
    print("현재 실행 중인 대화 전체를 기억합니다.")
    print("=" * 60)

    show_help()

    if USE_PROMPT_TOOLKIT:
        print("(입력 편집 기능 활성화)\n")
    else:
        print("(기본 입력 모드)\n")

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

            if user_input == "/help":
                show_help()
                continue

            if user_input == "/quit":
                print("(대화 종료)")
                break

            # 등록되지 않은 슬래시 명령어를 모델에 보내지 않음
            if user_input.startswith("/"):
                print("알 수 없는 명령어입니다. /help로 확인하세요.\n")
                continue

            print("Bot: ", end="", flush=True)
            response = chat(user_input)
            print(response)
            print()

        except (KeyboardInterrupt, EOFError):
            print("\n(대화 종료)")
            break

        except Exception as error:
            print(f"\n오류 발생: {error}")
            print("(실패한 질문은 대화 기록에 저장되지 않습니다.)\n")


if __name__ == "__main__":
    main()