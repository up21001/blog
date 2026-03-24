---
title: "AutoGen으로 멀티 에이전트 시스템 구축하기 — Microsoft AI 프레임워크 실전"
date: 2024-10-26T08:00:00+09:00
lastmod: 2024-11-02T08:00:00+09:00
description: "Microsoft AutoGen 프레임워크로 멀티 에이전트 시스템을 구축하는 방법을 실전 예시와 함께 설명합니다. UserProxyAgent, AssistantAgent, GroupChat 구조와 코드 실행 에이전트 설정을 다룹니다."
slug: "autogen-multi-agent-system-microsoft-guide"
categories: ["ai-agents"]
tags: ["AutoGen", "멀티 에이전트", "Microsoft", "AI 프레임워크", "LLM"]
series: []
draft: false
---

AI 에이전트 하나가 모든 것을 처리하던 시대는 빠르게 저물고 있습니다. 복잡한 업무일수록 여러 전문가가 협력해 처리하듯, AI 시스템도 역할을 나눈 에이전트들이 협업하는 구조가 훨씬 효과적이라는 사실이 실증되고 있습니다. Microsoft가 오픈소스로 공개한 **AutoGen**은 이 멀티 에이전트 패러다임을 가장 직관적으로 구현할 수 있는 프레임워크입니다.

필자는 실제 업무에서 AutoGen을 활용해 코드 리뷰 자동화, 데이터 분석 파이프라인, 기술 문서 생성 등의 작업을 자동화해 봤습니다. 처음에는 단순히 "에이전트 여러 개를 쓰는 것"이라고 생각했는데, 실제로 써보면 에이전트 간 대화 구조를 설계하는 것 자체가 소프트웨어 아키텍처만큼 중요하다는 것을 깨닫게 됩니다.

![AutoGen 멀티 에이전트 시스템 구조](/images/autogen-multi-agent-system.svg)

## AutoGen이란 무엇인가요?

AutoGen은 Microsoft Research가 개발한 오픈소스 멀티 에이전트 프레임워크입니다. 2023년 논문 "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"과 함께 공개되었으며, 현재 v0.4 계열(AutoGen 0.4, AG2)까지 발전하면서 프로덕션 사용을 고려한 구조 개편이 이루어졌습니다.

핵심 철학은 단순합니다. **"LLM 에이전트들이 서로 대화하면서 문제를 해결한다."** 각 에이전트는 고유한 역할과 능력을 갖고 있고, 이들의 대화 흐름이 곧 문제 해결 과정이 됩니다.

AutoGen이 다른 프레임워크와 차별화되는 지점은 세 가지입니다.

첫째, **대화 기반 설계**입니다. 에이전트 간 상호작용이 메시지 교환으로 이루어지기 때문에, 기존 채팅 UI 패러다임에 익숙한 개발자라면 매우 직관적으로 이해할 수 있습니다.

둘째, **코드 실행 통합**입니다. LLM이 생성한 코드를 즉시 실행하고 결과를 피드백으로 활용하는 루프가 기본 내장되어 있습니다. Docker 컨테이너나 로컬 환경에서 안전하게 코드를 실행할 수 있습니다.

셋째, **유연한 확장성**입니다. 기본 에이전트 타입을 상속해서 커스텀 에이전트를 만들거나, 외부 도구를 함수로 등록하는 것이 매우 간단합니다.

## 핵심 에이전트 타입 이해하기

AutoGen의 기본 빌딩 블록은 두 가지 에이전트 타입입니다.

### UserProxyAgent

사용자를 대리하는 에이전트입니다. 이름 때문에 헷갈릴 수 있는데, 실제로는 두 가지 역할을 동시에 합니다.

```python
from autogen import UserProxyAgent

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",   # ALWAYS / TERMINATE / NEVER
    max_consecutive_auto_reply=10,
    code_execution_config={
        "work_dir": "workspace",
        "use_docker": False,  # True 권장 (보안)
    },
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)
```

`human_input_mode`가 핵심입니다.

- `ALWAYS`: 매 응답마다 실제 사용자 입력을 기다립니다. Human-in-the-loop 패턴에 적합합니다.
- `TERMINATE`: 종료 조건 충족 시에만 입력을 받습니다.
- `NEVER`: 완전 자동화. LLM이 생성한 응답을 자동으로 처리합니다.

코드 실행 기능이 내장되어 있어서, AssistantAgent가 Python 코드를 생성하면 UserProxyAgent가 이를 실행하고 결과를 다시 대화에 주입합니다.

### AssistantAgent

LLM을 기반으로 동작하는 에이전트입니다. 계획 수립, 코드 작성, 분석, 답변 생성 등 지적 작업을 담당합니다.

```python
from autogen import AssistantAgent

assistant = AssistantAgent(
    name="assistant",
    llm_config={
        "model": "gpt-4o",
        "api_key": "YOUR_OPENAI_API_KEY",
        "temperature": 0,
    },
    system_message="""당신은 데이터 분석 전문가입니다.
    Python 코드를 작성해 데이터를 분석하고,
    결과를 명확하게 설명합니다.
    모든 작업이 완료되면 반드시 'TERMINATE'로 대화를 종료합니다.""",
)
```

`system_message`로 에이전트의 페르소나와 행동 지침을 정의합니다. 여기서 "TERMINATE" 키워드를 명시하는 것이 중요합니다. 종료 조건 없이 에이전트가 무한 루프에 빠지는 것을 방지하기 위해서입니다.

### 기본 양자 대화 시작하기

```python
# 대화 시작
user_proxy.initiate_chat(
    assistant,
    message="pandas를 사용해서 다음 CSV 파일을 분석하고 요약 통계를 출력해주세요: sales_data.csv",
)
```

이 한 줄이면 에이전트 간 대화가 시작됩니다. AssistantAgent가 코드를 작성하면, UserProxyAgent가 코드를 실행하고 결과를 전달합니다. AssistantAgent가 결과를 분석하고 추가 코드가 필요하면 다시 작성합니다. 이 루프가 종료 조건에 도달할 때까지 반복됩니다.

## GroupChat으로 3인 이상 협업 구성하기

실제 복잡한 작업에서는 두 에이전트만으로는 한계가 있습니다. AutoGen의 `GroupChat`을 사용하면 여러 에이전트가 한 대화에 참여하는 구조를 만들 수 있습니다.

```python
from autogen import GroupChat, GroupChatManager

# 에이전트 정의
researcher = AssistantAgent(
    name="researcher",
    llm_config=llm_config,
    system_message="""당신은 리서처입니다.
    주어진 주제를 조사하고 핵심 정보를 수집합니다.
    조사 완료 후 'RESEARCH_DONE'을 출력합니다.""",
)

writer = AssistantAgent(
    name="writer",
    llm_config=llm_config,
    system_message="""당신은 기술 작가입니다.
    리서처가 수집한 정보를 바탕으로 블로그 포스트를 작성합니다.
    작성 완료 후 'WRITING_DONE'을 출력합니다.""",
)

reviewer = AssistantAgent(
    name="reviewer",
    llm_config=llm_config,
    system_message="""당신은 편집자입니다.
    작성된 글을 검토하고 개선점을 제안합니다.
    최종 승인 시 'TERMINATE'를 출력합니다.""",
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

# GroupChat 설정
group_chat = GroupChat(
    agents=[user_proxy, researcher, writer, reviewer],
    messages=[],
    max_round=20,
    speaker_selection_method="auto",  # LLM이 다음 발화자를 결정
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
)

# 대화 시작
user_proxy.initiate_chat(
    manager,
    message="AutoGen 프레임워크에 대한 기술 블로그 포스트를 작성해주세요.",
)
```

`speaker_selection_method`는 그룹 채팅에서 다음 발화자를 결정하는 방식입니다.

- `"auto"`: GroupChatManager(LLM)가 상황에 맞는 다음 발화자를 선택합니다. 가장 유연하지만 API 비용이 추가됩니다.
- `"round_robin"`: 순서대로 돌아가며 발화합니다. 예측 가능하지만 상황 적응력이 떨어집니다.
- `"random"`: 무작위 선택입니다. 테스트 용도로 적합합니다.
- 커스텀 함수: 복잡한 라우팅 로직이 필요할 때 직접 함수를 작성합니다.

## 코드 실행 에이전트 안전하게 설정하기

AutoGen의 강력한 기능 중 하나는 LLM이 생성한 코드를 실제로 실행한다는 점입니다. 하지만 이것은 보안 위험이기도 합니다. 프로덕션 환경에서는 반드시 Docker 기반 실행을 사용해야 합니다.

```python
# Docker 기반 코드 실행 설정
user_proxy = UserProxyAgent(
    name="executor",
    human_input_mode="NEVER",
    code_execution_config={
        "executor": "docker",
        "work_dir": "/tmp/autogen_workspace",
        "timeout": 60,
        "use_docker": "python:3.11-slim",  # 격리된 컨테이너
        "bind_volume": False,  # 호스트 파일시스템 마운트 차단
    },
)
```

코드 실행 에이전트를 설계할 때 필자가 겪은 몇 가지 실수를 공유합니다.

**실수 1: 타임아웃 미설정.** 에이전트가 무한 루프 코드를 생성하면 작업이 영구적으로 멈춥니다. `timeout` 값을 반드시 설정하세요.

**실수 2: 너무 관대한 종료 조건.** `is_termination_msg` 함수가 너무 쉽게 트리거되면 작업이 완료되기 전에 대화가 끊깁니다. 반대로 너무 엄격하면 불필요한 라운드가 많아집니다.

**실수 3: system_message 과부하.** 에이전트 하나에 너무 많은 역할과 지침을 넣으면 LLM이 혼란스러워합니다. 역할을 명확히 분리하고 각 에이전트의 system_message를 간결하게 유지하세요.

## 함수 도구 등록하기

에이전트가 외부 API를 호출하거나 특정 기능을 수행하도록 함수 도구를 등록할 수 있습니다.

```python
from autogen import register_function

# 웹 검색 함수 정의
def search_web(query: str) -> str:
    """웹에서 정보를 검색합니다."""
    # 실제 구현에서는 SerpAPI, Tavily 등을 사용
    results = tavily_client.search(query, max_results=5)
    return "\n".join([r["content"] for r in results["results"]])

# 에이전트에 함수 등록
register_function(
    search_web,
    caller=assistant,      # 함수를 호출할 에이전트
    executor=user_proxy,   # 함수를 실행할 에이전트
    name="search_web",
    description="주어진 쿼리로 인터넷을 검색하고 결과를 반환합니다.",
)
```

`caller`와 `executor`를 분리하는 설계가 흥미롭습니다. LLM(caller)이 어떤 도구를 쓸지 결정하고, UserProxyAgent(executor)가 실제로 실행합니다. 이 분리 덕분에 함수 실행 권한을 세밀하게 제어할 수 있습니다.

## 실전 예시: 데이터 분석 파이프라인

실제 업무에서 유용한 데이터 분석 파이프라인을 구성해 보겠습니다. 세 가지 역할을 가진 에이전트가 협력합니다.

```python
import autogen

llm_config = {"model": "gpt-4o", "api_key": "YOUR_KEY", "temperature": 0}

# 1. 데이터 엔지니어: 데이터 로딩과 전처리
data_engineer = autogen.AssistantAgent(
    name="data_engineer",
    llm_config=llm_config,
    system_message="""데이터 엔지니어로서 CSV/JSON 데이터를 로딩하고
    결측치 처리, 타입 변환 등 전처리 작업을 수행합니다.
    pandas 코드를 작성하며, 완료 시 'DATA_READY'를 출력합니다.""",
)

# 2. 데이터 사이언티스트: 분석과 시각화
data_scientist = autogen.AssistantAgent(
    name="data_scientist",
    llm_config=llm_config,
    system_message="""데이터 사이언티스트로서 전처리된 데이터를 분석하고
    통계 분석, 상관관계 분석, matplotlib 시각화를 수행합니다.
    인사이트 도출 완료 시 'ANALYSIS_DONE'을 출력합니다.""",
)

# 3. 리포트 작성자: 결과 문서화
report_writer = autogen.AssistantAgent(
    name="report_writer",
    llm_config=llm_config,
    system_message="""분석 결과를 바탕으로 경영진이 이해하기 쉬운
    마크다운 형식의 분석 리포트를 작성합니다.
    리포트 완성 후 'TERMINATE'를 출력합니다.""",
)

executor = autogen.UserProxyAgent(
    name="executor",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "analysis_workspace", "use_docker": False},
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
)

# GroupChat 구성
gc = autogen.GroupChat(
    agents=[executor, data_engineer, data_scientist, report_writer],
    messages=[],
    max_round=30,
    speaker_selection_method="auto",
)

manager = autogen.GroupChatManager(groupchat=gc, llm_config=llm_config)

# 분석 시작
executor.initiate_chat(
    manager,
    message="""
    sales_2025.csv 파일을 분석해주세요.
    - 월별 매출 트렌드 분석
    - 상위 5개 제품 카테고리 분석
    - 전년 대비 성장률 계산
    - 시각화 포함
    결과를 마크다운 리포트로 정리해주세요.
    """,
)
```

이 구조가 단일 에이전트 접근법과 다른 점은 각 에이전트가 자신의 전문 영역에서 최적화된 결과를 내고, 그 결과가 다음 에이전트의 입력이 된다는 것입니다. 마치 실제 데이터 팀처럼 작동합니다.

## AutoGen 0.4의 새로운 구조

AutoGen 0.4(AG2)는 기존 버전과 상당히 다른 구조를 가집니다. 주요 변화점을 정리합니다.

**새로운 에이전트 모델**: `ConversableAgent` 기반의 단일 계층 구조에서 `BaseAgent` → `RoutedAgent` 형태의 메시지 라우팅 기반 구조로 전환되었습니다.

**런타임 분리**: `SingleThreadedAgentRuntime`과 `GrpcWorkerAgentRuntime`을 제공하여 단일 프로세스와 분산 실행을 선택할 수 있습니다.

```python
# AutoGen 0.4 스타일
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o")

agent = AssistantAgent(name="assistant", model_client=model_client)
team = RoundRobinGroupChat([agent])

# async 기반 실행
import asyncio
asyncio.run(team.run(task="Hello, write a Python hello world."))
```

0.4는 `async/await` 기반으로 완전히 재설계되어 대규모 병렬 에이전트 처리가 훨씬 용이해졌습니다. 신규 프로젝트라면 0.4 계열로 시작하는 것을 권장합니다.

## 실전 팁과 주의사항

13년 차 엔지니어로서 AutoGen을 실무에 도입하면서 정리한 핵심 팁입니다.

**비용 관리**: GroupChat에서 `speaker_selection_method="auto"`를 쓰면 매 라운드마다 GroupChatManager가 LLM을 호출합니다. 에이전트가 많을수록 비용이 선형 이상으로 증가합니다. 가능하면 `round_robin`이나 커스텀 함수를 우선 검토하세요.

**컨텍스트 윈도우 관리**: 대화 히스토리가 길어질수록 LLM 컨텍스트를 많이 차지합니다. `max_round`를 적절히 설정하고, 필요한 경우 대화 요약 에이전트를 추가하는 것이 좋습니다.

**에이전트 수 최적화**: 에이전트가 많다고 좋은 것이 아닙니다. 3~5개 에이전트가 명확한 역할 분담을 가질 때 가장 효율적입니다. 역할이 불명확한 에이전트를 추가하면 오히려 혼선이 생깁니다.

**로깅과 디버깅**: `autogen.runtime_logging` 모듈로 대화 로그를 SQLite에 저장할 수 있습니다. 문제 추적과 비용 분석에 필수적입니다.

```python
import autogen.runtime_logging

logging_session_id = autogen.runtime_logging.start(
    logger_type="sqlite",
    config={"dbname": "autogen_logs.db"},
)
# ... 에이전트 실행 ...
autogen.runtime_logging.stop()
```

## 마치며

AutoGen은 멀티 에이전트 시스템 구축의 진입 장벽을 크게 낮춘 프레임워크입니다. "에이전트들이 대화로 문제를 해결한다"는 직관적인 모델 덕분에, LLM API 경험이 있는 개발자라면 하루 이틀 안에 첫 프로토타입을 만들 수 있습니다.

다만 프로덕션 도입 시에는 비용, 지연 시간, 신뢰성 측면을 반드시 검토해야 합니다. 모든 작업에 멀티 에이전트가 필요한 것은 아닙니다. 단순한 작업에는 단일 에이전트 혹은 일반 LLM 호출이 훨씬 경제적입니다.

복잡한 작업 파이프라인, 코드 생성과 실행이 반복되는 작업, 여러 전문 지식이 필요한 작업이라면 AutoGen을 적극적으로 검토해 보세요. 특히 코드 실행 에이전트가 내장된 프레임워크는 AutoGen만의 강점입니다.

다음 편에서는 CrewAI를 다루겠습니다. AutoGen이 대화 흐름 중심이라면, CrewAI는 역할과 목표 중심의 설계 철학을 가집니다. 두 프레임워크를 비교하면서 각각 어떤 상황에 적합한지 판단하는 기준을 갖추시기 바랍니다.
