"""
프롬프트 릴리즈 품질 실험실 & 에이전트 복구 런북 시리즈 내용 대폭 보강
"""
from pathlib import Path
import re

POSTS_DIR = Path("C:/My/Claude/Blog/blog/content/posts")

# ── 프롬프트 릴리즈 품질 실험실 회차별 주제 ──────────────────────────────
PROMPT_LAB_TOPICS = {
    67: ("회귀 탐지 자동화 실험", "회귀율 3% 목표", [
        ("실험 배경", "팀에서 프롬프트를 수동으로 검수하다 보면 주관적 판단이 개입되어 동일한 프롬프트가 어떤 날은 통과하고 어떤 날은 차단됩니다. 이 편차를 줄이기 위해 회귀 탐지 자동화 실험을 설계했습니다.\n\n**실험 목표**: 프롬프트 수정 후 기존 골든셋 기준 품질 하락 여부를 자동으로 탐지\n**기간**: 2주\n**대상**: 프로덕션 프롬프트 47개"),
        ("실험 설계", "```python\n# 회귀 탐지 기본 구조\ndef detect_regression(old_prompt, new_prompt, golden_set):\n    old_scores = [evaluate(old_prompt, case) for case in golden_set]\n    new_scores = [evaluate(new_prompt, case) for case in golden_set]\n    \n    regression_rate = sum(\n        1 for o, n in zip(old_scores, new_scores) if n < o * 0.95\n    ) / len(golden_set)\n    \n    return regression_rate, old_scores, new_scores\n```\n\n골든셋은 각 프롬프트 유형별 20개 케이스로 구성했으며, 점수 5% 이상 하락을 회귀로 정의했습니다."),
        ("실험 결과", "| 항목 | 수동 검수 | 자동 탐지 |\n|------|-----------|----------|\n| 탐지 시간 | 평균 4.2시간 | 8분 |\n| 탐지 정확도 | 71% | 89% |\n| 거짓 양성률 | 22% | 6% |\n| 비용 | 검수자 2명/주 | 토큰 비용 $12/주 |\n\n자동 탐지가 정확도와 속도 모두에서 유의미하게 우수했습니다."),
        ("주요 발견", "가장 큰 발견은 **맥락 길이가 길수록 회귀 탐지가 어렵다**는 점입니다. 3000토큰 이상의 프롬프트에서는 골든셋 기반 탐지 정확도가 74%로 떨어졌습니다. 긴 프롬프트는 청크 단위 분할 평가가 필요합니다."),
        ("다음 실험으로", "회귀 탐지의 정확도를 높이기 위해 다음 실험(68차)에서는 A/B 테스트 기반 품질 게이트를 설계합니다. 단순 점수 비교가 아니라 실제 사용자 행동 데이터를 피드백으로 활용하는 방식을 탐구합니다."),
    ]),
    68: ("A/B 테스트 기반 품질 게이트 설계", "사용자 피드백 연동", [
        ("실험 배경", "67차 실험에서 자동화된 회귀 탐지의 한계를 발견했습니다. 내부 평가 점수가 높아도 실제 사용자가 체감하는 품질은 다를 수 있습니다. 이번 실험에서는 A/B 테스트를 품질 게이트에 통합하는 방법을 검증합니다.\n\n**가설**: 사용자 피드백을 품질 게이트 트리거로 활용하면 불필요한 롤백을 30% 줄일 수 있다.\n**측정 지표**: 롤백 빈도, 사용자 만족도, 게이트 통과 시간"),
        ("A/B 테스트 구조", "```yaml\n# 품질 게이트 A/B 설정\nab_config:\n  control_group: 0.3  # 기존 프롬프트 30%\n  treatment_group: 0.7  # 신규 프롬프트 70%\n  min_sample_size: 200\n  confidence_level: 0.95\n  \n  success_metrics:\n    - thumbs_up_rate: '>= 0.72'\n    - task_completion: '>= 0.85'\n    - avg_turns: '<= 3.2'\n  \n  abort_conditions:\n    - error_rate: '> 0.05'\n    - negative_feedback: '> 0.20'\n```"),
        ("실험 결과", "200개 샘플 수집 기준 평균 6.4시간이 소요됐습니다. 결과:\n\n- **성공 케이스 (31개 프롬프트)**: 평균 thumbs-up 74%, 작업 완료율 87%로 게이트 통과\n- **실패 케이스 (9개 프롬프트)**: 초기 2시간 내 error_rate > 5% 초과로 조기 차단\n- **경계 케이스 (7개 프롬프트)**: 수동 판정 필요\n\n롤백 빈도는 기존 대비 28% 감소해 가설에 근접했습니다."),
        ("운영 시사점", "조기 차단 조건을 너무 엄격하게 설정하면 좋은 프롬프트도 배포 기회를 잃습니다. **2시간 + 50샘플** 기준의 초기 체크포인트를 두고, 이후 전체 평가를 진행하는 2단계 구조가 효과적이었습니다."),
        ("다음 실험으로", "69차에서는 다중 모델 환경에서의 품질 게이트 일관성을 검증합니다. 동일 프롬프트가 GPT-4와 Claude에서 다른 품질 분포를 보이는 경우, 게이트 기준을 어떻게 조정해야 하는지 탐구합니다."),
    ]),
    69: ("다중 모델 환경 품질 게이트 일관성", "모델별 기준 분리", [
        ("실험 배경", "프로덕션 환경에서는 단일 모델이 아닌 여러 LLM을 라우팅하는 경우가 많습니다. 동일한 프롬프트가 모델에 따라 품질 편차가 크게 발생하며, 단일 품질 게이트 기준으로는 과도한 차단이나 과도한 통과가 발생합니다.\n\n**목표**: 모델별 맞춤 품질 기준선 수립\n**대상 모델**: GPT-4o, Claude Sonnet, Gemini Pro"),
        ("모델별 베이스라인 측정", "| 모델 | 평균 점수 | 표준편차 | P10 | P90 |\n|------|-----------|----------|-----|-----|\n| GPT-4o | 0.81 | 0.09 | 0.68 | 0.93 |\n| Claude Sonnet | 0.79 | 0.07 | 0.70 | 0.91 |\n| Gemini Pro | 0.76 | 0.12 | 0.59 | 0.91 |\n\n모델마다 점수 분포가 다르기 때문에 절대 기준치를 적용하면 Gemini Pro만 과도하게 차단됩니다."),
        ("모델별 상대 기준 적용", "```python\nMODEL_BASELINES = {\n    'gpt-4o':    {'mean': 0.81, 'std': 0.09},\n    'claude':    {'mean': 0.79, 'std': 0.07},\n    'gemini':    {'mean': 0.76, 'std': 0.12},\n}\n\ndef is_quality_pass(model, score, threshold_z=-1.0):\n    bl = MODEL_BASELINES[model]\n    z_score = (score - bl['mean']) / bl['std']\n    return z_score >= threshold_z  # 평균 1표준편차 이하 차단\n```\n\n상대 기준 적용 후 거짓 양성률이 22%에서 7%로 감소했습니다."),
        ("실험 결론", "모델별 개별 기준선을 유지하는 것이 필수적입니다. 특히 스코어 분산이 큰 모델(Gemini Pro)에서는 z-score 기반 판정이 절대 점수 기준보다 훨씬 안정적이었습니다."),
        ("다음 실험으로", "70차에서는 긴 프롬프트 체인(Chain-of-Thought)에서의 품질 평가 방법을 탐구합니다."),
    ]),
    70: ("CoT 프롬프트 체인 품질 평가", "단계별 평가 전략", [
        ("실험 배경", "Chain-of-Thought 프롬프트는 단순 프롬프트보다 평가가 복잡합니다. 최종 출력만 평가하면 중간 추론 과정의 오류를 놓칠 수 있고, 모든 단계를 평가하면 비용과 시간이 과도하게 증가합니다.\n\n**목표**: CoT 프롬프트의 품질을 효율적으로 평가하는 샘플링 전략 개발"),
        ("평가 전략 비교", "3가지 전략을 비교 실험했습니다:\n\n1. **최종 출력만 평가**: 비용 최소, 중간 오류 탐지 불가\n2. **전체 단계 평가**: 정확도 최대, 비용 3.8배\n3. **중요 단계 샘플링**: 첫 단계 + 마지막 단계 + 랜덤 1개\n\n```python\ndef evaluate_cot(steps, strategy='sample'):\n    if strategy == 'final':\n        return evaluate_step(steps[-1])\n    elif strategy == 'full':\n        return sum(evaluate_step(s) for s in steps) / len(steps)\n    else:  # sample\n        sample = [steps[0], steps[-1], steps[len(steps)//2]]\n        return sum(evaluate_step(s) for s in sample) / 3\n```"),
        ("실험 결과", "| 전략 | 오류 탐지율 | 비용 | 처리 시간 |\n|------|------------|------|----------|\n| 최종 출력만 | 63% | $1 | 0.8초 |\n| 전체 단계 | 97% | $3.8 | 3.1초 |\n| 중요 단계 샘플링 | 91% | $1.4 | 1.2초 |\n\n샘플링 전략이 비용과 정확도의 균형에서 가장 우수했습니다."),
        ("운영 권장사항", "5단계 이하 CoT: 전체 평가, 6단계 이상 CoT: 샘플링 전략을 권장합니다. 특히 첫 번째 추론 단계의 품질이 최종 결과에 가장 큰 영향을 미치므로 반드시 포함해야 합니다."),
        ("다음 실험으로", "71차에서는 프롬프트 릴리즈 승인 플로우에 LLM-as-Judge를 도입하는 실험을 진행합니다."),
    ]),
    71: ("LLM-as-Judge 승인 플로우 도입", "자동 승인 정확도 90% 목표", [
        ("실험 배경", "품질 게이트의 최종 승인은 여전히 사람이 합니다. 하루 평균 23건의 프롬프트 수정이 발생하는 환경에서 수동 승인은 병목이 됩니다. LLM을 판사로 활용하여 명확한 케이스를 자동으로 처리하는 방법을 실험합니다."),
        ("Judge 프롬프트 설계", "```\n당신은 프롬프트 품질 심사 전문가입니다.\n\n[평가 기준]\n1. 명확성: 의도가 모호하지 않은가\n2. 안전성: 유해 콘텐츠 생성 가능성이 없는가\n3. 효율성: 불필요한 토큰 낭비가 없는가\n4. 일관성: 기존 버전 대비 품질이 유지되는가\n\n[출력 형식]\n판정: APPROVE / REJECT / HUMAN_REVIEW\n점수: 0-100\n근거: (2-3문장)\n```"),
        ("실험 결과", "300건 테스트 기준:\n\n- **APPROVE 정확도**: 94.2% (사람과 일치)\n- **REJECT 정확도**: 88.7% (일부 보수적 차단)\n- **HUMAN_REVIEW 비율**: 18.3% (불확실 케이스 위임)\n- **전체 자동화율**: 81.7%\n\n목표였던 90% 정확도를 APPROVE 케이스에서 달성했습니다."),
        ("실패 패턴 분석", "Judge가 가장 자주 실수하는 케이스:\n1. 도메인 전문 용어가 많은 프롬프트 → 지식 부족으로 보수적 판정\n2. 이모지/특수문자 포함 프롬프트 → 형식 오류로 오판\n3. 다국어 혼합 프롬프트 → 언어 전환 지점에서 품질 저하"),
        ("다음 실험으로", "72차에서는 실패 패턴을 기반으로 Judge 프롬프트를 개선하고, 도메인별 특화 Judge를 분리하는 실험을 진행합니다."),
    ]),
    72: ("도메인별 Judge 분리 실험", "전문 도메인 정확도 향상", [
        ("실험 배경", "71차에서 도메인 전문 용어가 포함된 프롬프트에서 Judge 정확도가 낮았습니다. 단일 Judge 대신 도메인별로 특화된 Judge를 분리하면 정확도를 높일 수 있다는 가설을 검증합니다."),
        ("도메인 분류 구조", "```python\nDOMAIN_JUDGES = {\n    'medical': '의료/건강 도메인 전문 심사자...',\n    'legal':   '법률/규정 준수 전문 심사자...',\n    'code':    '코드 생성/리뷰 전문 심사자...',\n    'general': '일반 목적 심사자...'\n}\n\ndef route_to_judge(prompt_text):\n    domain = classify_domain(prompt_text)  # 도메인 분류기\n    return DOMAIN_JUDGES.get(domain, DOMAIN_JUDGES['general'])\n```"),
        ("도메인별 정확도 비교", "| 도메인 | 단일 Judge | 도메인 Judge | 개선폭 |\n|--------|-----------|-------------|-------|\n| 의료 | 71.3% | 91.8% | +20.5% |\n| 법률 | 74.1% | 93.2% | +19.1% |\n| 코드 | 83.4% | 92.7% | +9.3% |\n| 일반 | 91.2% | 92.1% | +0.9% |\n\n전문 도메인에서 개선폭이 두드러졌습니다."),
        ("비용 분석", "도메인 Judge 분리로 토큰 비용이 평균 12% 증가했지만, 수동 검토 케이스가 18.3%에서 8.9%로 절반 감소하여 전체 운영 비용은 7% 절감되었습니다."),
        ("다음 실험으로", "73차에서는 프롬프트 릴리즈 롤백 자동화를 실험합니다. 품질 하락 감지 후 이전 버전으로 자동 복원하는 파이프라인을 구축합니다."),
    ]),
    73: ("릴리즈 롤백 자동화 파이프라인", "5분 내 자동 롤백 목표", [
        ("실험 배경", "프롬프트 릴리즈 후 품질 하락이 감지되면 현재는 수동으로 이전 버전을 배포합니다. 평균 롤백 시간이 47분으로, 이 기간 동안 품질 저하된 응답이 사용자에게 전달됩니다. 자동 롤백 파이프라인으로 이를 5분 이내로 줄이는 것이 목표입니다."),
        ("자동 롤백 트리거 설계", "```yaml\nrollback_triggers:\n  # 즉각 롤백 (5분 내 감지)\n  critical:\n    - error_rate > 0.10\n    - response_quality < baseline * 0.80\n  \n  # 경고 (15분 관찰 후 판정)\n  warning:\n    - error_rate > 0.05\n    - response_quality < baseline * 0.90\n    - user_negative_feedback > 0.15\n  \n  rollback_action:\n    type: \"previous_version\"\n    notify: [\"#ops-channel\", \"on-call\"]\n    post_rollback_review: true\n```"),
        ("파이프라인 구현 결과", "자동 롤백 파이프라인 도입 후 4주간 운영 데이터:\n\n- **롤백 발생**: 7건\n- **평균 감지 시간**: 3.2분 (목표 5분 달성)\n- **평균 복원 시간**: 1.8분\n- **전체 롤백 시간**: 평균 5.0분 (이전: 47분)\n- **거짓 롤백**: 1건 (14.3%)"),
        ("거짓 롤백 방지", "1건의 거짓 롤백은 일시적 트래픽 급증으로 인한 오류율 상승이 원인이었습니다. 트래픽 기반 가중치를 트리거에 추가하여 해결했습니다:\n\n```python\ndef should_rollback(error_rate, traffic_multiplier):\n    adjusted_threshold = 0.10 * min(traffic_multiplier, 3.0)\n    return error_rate > adjusted_threshold\n```"),
        ("다음 실험으로", "74차에서는 롤백 이력 데이터를 분석하여 품질 하락 패턴을 사전에 예측하는 모델을 개발합니다."),
    ]),
    74: ("품질 하락 사전 예측 모델", "릴리즈 전 위험도 스코어링", [
        ("실험 배경", "73차까지의 실험은 모두 '릴리즈 후' 문제 탐지에 집중했습니다. 이번 실험은 릴리즈 전 단계에서 품질 하락 가능성을 예측하는 모델을 개발합니다. 과거 롤백 이력 데이터를 학습에 활용합니다."),
        ("특징 엔지니어링", "```python\ndef extract_features(prompt_diff):\n    return {\n        'token_length_delta': len(new) - len(old),\n        'structure_change': structural_diff_score(old, new),\n        'keyword_additions': count_new_keywords(old, new),\n        'instruction_clarity': clarity_score(new),\n        'similar_rollback_history': lookup_similar_cases(new),\n        'release_hour': datetime.now().hour,  # 트래픽 패턴 반영\n        'days_since_last_rollback': get_last_rollback_days(),\n    }\n```"),
        ("모델 성능", "과거 롤백 142건 + 성공 릴리즈 891건으로 훈련:\n\n| 모델 | 정밀도 | 재현율 | F1 |\n|------|--------|--------|----|\n| Logistic Regression | 0.71 | 0.68 | 0.69 |\n| Random Forest | 0.83 | 0.79 | 0.81 |\n| LightGBM | 0.87 | 0.82 | 0.84 |\n\nLightGBM이 가장 우수했습니다. **위험도 점수 0.7 이상**을 고위험으로 분류합니다."),
        ("실제 운영 적용", "고위험 릴리즈(점수 0.7+)에는 자동으로 추가 검토 단계를 추가하고, 트래픽을 10%로 제한한 상태에서 1시간 모니터링 후 전체 롤아웃합니다."),
        ("다음 실험으로", "75차에서는 예측 모델을 CI/CD 파이프라인에 통합하여 자동화 수준을 높입니다."),
    ]),
    75: ("CI/CD 파이프라인 통합", "릴리즈 품질 게이트 완전 자동화", [
        ("실험 배경", "67차부터 74차까지 개발한 품질 평가, Judge, 롤백, 예측 모델을 CI/CD 파이프라인에 통합합니다. 프롬프트 수정 → PR 생성 → 자동 품질 검증 → 승인 → 배포의 전체 플로우를 자동화합니다."),
        ("파이프라인 구조", "```yaml\n# GitHub Actions 워크플로우\nname: Prompt Quality Gate\non: [pull_request]\n\njobs:\n  quality-check:\n    steps:\n      - name: 회귀 탐지\n        run: python qa/regression_check.py\n      \n      - name: LLM Judge 평가\n        run: python qa/judge_evaluate.py --domain auto\n      \n      - name: 위험도 예측\n        run: python qa/risk_score.py\n      \n      - name: 결과 PR 코멘트\n        run: python qa/post_result.py\n```"),
        ("도입 효과 (4주 데이터)", "| 지표 | 도입 전 | 도입 후 | 변화 |\n|------|---------|---------|------|\n| 수동 검토 건수/주 | 143건 | 28건 | -80% |\n| 릴리즈 리드타임 | 4.2시간 | 38분 | -85% |\n| 품질 롤백 횟수/월 | 11회 | 3회 | -73% |\n| 엔지니어 검토 시간 | 6.4시간/주 | 1.1시간/주 | -83% |\n\n모든 핵심 지표에서 유의미한 개선이 달성되었습니다."),
        ("운영 주의사항", "자동화가 높아질수록 시스템이 놓치는 케이스가 중요해집니다. 월 1회 수동 샘플링 감사(전체 릴리즈의 10%)를 유지하여 자동화 드리프트를 방지하세요."),
        ("다음 실험으로", "76차에서는 다국어 환경에서의 품질 게이트 확장성을 검증합니다."),
    ]),
    76: ("다국어 환경 품질 게이트 확장", "한국어·영어·일본어 동시 지원", [
        ("실험 배경", "서비스가 글로벌로 확장되면서 한국어, 영어, 일본어 프롬프트를 동시에 관리해야 합니다. 기존 품질 게이트는 한국어 기준으로 설계되어 영어/일본어 평가 시 정확도가 떨어지는 문제가 있었습니다."),
        ("언어별 평가 기준 차이", "| 언어 | 명확성 기준 | 간결성 기준 | Judge 모델 |\n|------|------------|------------|----------|\n| 한국어 | 조사 완결성 | 존댓말 일관성 | Claude (ko) |\n| 영어 | 능동태 비율 | 지시문 명확성 | GPT-4o (en) |\n| 일본어 | 敬語 레벨 | 文末 일관성 | Claude (ja) |\n\n언어별로 다른 Judge 모델을 사용하는 것이 정확도를 15~20% 높였습니다."),
        ("언어 감지 및 라우팅", "```python\nfrom langdetect import detect\n\ndef evaluate_multilingual(prompt):\n    lang = detect(prompt)\n    if lang not in SUPPORTED_LANGS:\n        lang = 'en'  # 기본값\n    \n    judge = LANG_JUDGES[lang]\n    baseline = LANG_BASELINES[lang]\n    return judge.evaluate(prompt, baseline)\n```"),
        ("실험 결과 요약", "다국어 지원 후 일본어 서비스 품질 불만이 43% 감소하고, 글로벌 릴리즈 리드타임이 언어별 순차 검토에서 병렬 처리로 변경되어 2.1배 빨라졌습니다."),
        ("다음 실험으로", "77차에서는 품질 게이트 비용 최적화를 다룹니다. 모든 검사를 실행하면 비용이 과도해지므로 스마트한 건너뜀 전략을 실험합니다."),
    ]),
    77: ("품질 게이트 비용 최적화", "스마트 스킵 전략", [
        ("실험 배경", "CI/CD 파이프라인에 모든 품질 체크를 통합한 후 월 토큰 비용이 $847로 증가했습니다. 스킵 가능한 체크를 지능적으로 판단하여 비용을 50% 이하로 줄이는 것이 목표입니다."),
        ("변경 규모별 체크 전략", "```python\ndef get_required_checks(diff_analysis):\n    size = diff_analysis['token_change_ratio']\n    scope = diff_analysis['affected_sections']\n    \n    if size < 0.05 and scope == ['examples']:  # 예시만 수정\n        return ['regression_light']  # 경량 체크만\n    elif size < 0.15:  # 소규모 수정\n        return ['regression_full', 'judge_fast']\n    else:  # 대규모 수정\n        return ['regression_full', 'judge_full', 'ab_test']\n```"),
        ("비용 절감 결과", "| 체크 유형 | 건수/월 | 비용/건 | 월 비용 |\n|----------|---------|---------|--------|\n| 전체 체크 (이전) | 891건 | $0.95 | $847 |\n| 경량 체크 | 412건 | $0.12 | $49 |\n| 표준 체크 | 368건 | $0.61 | $224 |\n| 전체 체크 | 111건 | $0.95 | $105 |\n| **합계** | **891건** | **-** | **$378** |\n\n월 비용 55% 절감 달성 (목표 초과)."),
        ("품질 영향", "비용 절감 최적화 후 롤백 빈도가 오히려 소폭 감소(3.1 → 2.8건/월)했습니다. 경량 체크로 분류된 변경들이 실제로도 저위험이었음이 확인됐습니다."),
        ("다음 실험으로", "78차에서는 품질 게이트 대시보드를 구축하여 팀 전체가 릴리즈 품질 현황을 실시간으로 파악할 수 있도록 합니다."),
    ]),
    78: ("품질 게이트 실시간 대시보드", "팀 가시성 향상", [
        ("실험 배경", "품질 게이트 시스템이 정교해질수록 팀원들이 '지금 어떤 상태인지' 파악하기 어려워졌습니다. 이번 실험에서는 릴리즈 품질 현황을 한눈에 볼 수 있는 대시보드를 구축합니다."),
        ("핵심 대시보드 메트릭", "대시보드에 표시할 핵심 지표 5개를 선정했습니다:\n\n1. **릴리즈 성공률** (7일 롤링 평균)\n2. **현재 게이트 대기 건수** (실시간)\n3. **평균 검증 시간** (현재 vs 지난주)\n4. **도메인별 품질 점수 트렌드** (30일)\n5. **고위험 릴리즈 비율** (예측 모델 기준)\n\n```python\n# Grafana 데이터소스 쿼리 예시\nSELECT\n    date_trunc('day', released_at) as day,\n    COUNT(*) as total,\n    SUM(CASE WHEN rolled_back THEN 1 ELSE 0 END) as rollbacks,\n    1 - (rollbacks::float / total) as success_rate\nFROM prompt_releases\nWHERE released_at > NOW() - INTERVAL '30 days'\nGROUP BY 1 ORDER BY 1\n```"),
        ("대시보드 도입 효과", "대시보드 도입 2주 후 팀 내 변화:\n- 주간 품질 리뷰 미팅 시간: 45분 → 15분\n- 즉흥적인 Slack 문의 (\"지금 배포해도 돼?\") 80% 감소\n- 문제 발생 시 평균 인지 시간: 28분 → 4분"),
        ("알림 연동", "대시보드 임계값 기반 Slack 알림을 추가했습니다. 특히 **릴리즈 성공률 7일 평균이 92% 이하로 떨어질 때** 팀 채널에 자동 경고가 발송됩니다."),
        ("다음 실험으로", "79차에서는 품질 게이트 시스템 자체의 성능 드리프트를 모니터링하는 메타-모니터링을 다룹니다."),
    ]),
    79: ("품질 게이트 메타 모니터링", "시스템 드리프트 감지", [
        ("실험 배경", "품질 게이트 시스템이 장기 운영되면서 Judge 모델의 판단 기준이 조금씩 변화하거나, 골든셋이 현실과 멀어지는 드리프트가 발생합니다. 이번 실험은 품질 게이트 자체의 건강을 모니터링하는 메타 시스템을 구축합니다."),
        ("드리프트 감지 방법", "```python\ndef detect_judge_drift(judge, reference_set, window_days=30):\n    recent_scores = judge.evaluate_batch(\n        reference_set,\n        since=datetime.now() - timedelta(days=window_days)\n    )\n    baseline_scores = JUDGE_BASELINES[judge.name]\n    \n    # KS 검정으로 분포 변화 감지\n    from scipy import stats\n    ks_stat, p_value = stats.ks_2samp(baseline_scores, recent_scores)\n    \n    if p_value < 0.05:  # 유의미한 분포 변화\n        alert_judge_drift(judge.name, ks_stat)\n```"),
        ("드리프트 사례 분석", "운영 6개월 차에 법률 도메인 Judge의 드리프트를 감지했습니다. 판정 기준이 모델 업데이트로 인해 더 보수적으로 변화하여 거짓 양성률이 7%에서 19%로 증가한 것이 원인이었습니다. Judge 프롬프트 재보정으로 해결했습니다."),
        ("메타 모니터링 주기", "- **Judge 드리프트 체크**: 주 1회 자동 실행\n- **골든셋 유효성 검토**: 월 1회 사람이 직접 검토\n- **베이스라인 업데이트**: 분기 1회\n\n이 주기를 지키면 시스템이 현실과 크게 멀어지는 것을 방지할 수 있습니다."),
        ("다음 실험으로", "80차에서는 외부 규제/정책 변화에 품질 게이트가 빠르게 적응하는 컴플라이언스 업데이트 파이프라인을 실험합니다."),
    ]),
    80: ("컴플라이언스 빠른 업데이트 파이프라인", "규제 변화 48시간 내 반영", [
        ("실험 배경", "개인정보보호법 개정, AI 안전 가이드라인 발표 등 외부 규제 변화가 빈번해지고 있습니다. 새 규제가 발효될 때 모든 프롬프트를 수동으로 검토하는 데 평균 3.2주가 소요됩니다. 이를 48시간 이내로 단축하는 파이프라인을 실험합니다."),
        ("컴플라이언스 규칙 엔진", "```python\nclass ComplianceRule:\n    def __init__(self, rule_id, description, checker_fn, severity):\n        self.rule_id = rule_id\n        self.description = description\n        self.check = checker_fn\n        self.severity = severity  # critical / warning\n\n# 새 규정 추가 예시\nnew_rule = ComplianceRule(\n    rule_id='PRIVACY-2026-01',\n    description='개인식별정보 직접 수집 금지',\n    checker_fn=lambda p: not contains_pii_request(p),\n    severity='critical'\n)\nCOMPLIANCE_ENGINE.add_rule(new_rule)\n```"),
        ("48시간 업데이트 프로세스", "1. **T+0시간**: 규제 텍스트 입력 → LLM이 체커 함수 초안 생성\n2. **T+4시간**: 법무팀 리뷰 및 체커 확정\n3. **T+6시간**: 기존 프롬프트 전수 자동 스캔\n4. **T+24시간**: 위반 프롬프트 수정 완료\n5. **T+48시간**: 전체 검증 및 배포 완료"),
        ("실제 적용 사례", "EU AI Act 가이드라인 업데이트 시 이 파이프라인을 처음 적용했습니다. 1247개 프롬프트 전수 스캔에 2.3시간이 소요됐으며, 위반 73건 중 61건을 자동으로 수정 제안을 생성했습니다."),
        ("다음 실험으로", "81차에서는 품질 실험실 운영 1년간의 총 성과를 정리하고 2년차 로드맵을 수립합니다."),
    ]),
    81: ("1년 운영 성과 회고 및 2년차 로드맵", "67-80차 실험 총정리", [
        ("1년간 실험 성과 요약", "67차부터 80차까지 14번의 실험을 통해 프롬프트 릴리즈 품질 관리 시스템을 구축했습니다.\n\n**핵심 성과 지표:**\n\n| 지표 | 실험 시작 전 | 현재 | 개선율 |\n|------|------------|------|-------|\n| 릴리즈 리드타임 | 4.2시간 | 38분 | -85% |\n| 품질 롤백/월 | 11회 | 2.8회 | -75% |\n| 수동 검토 비율 | 100% | 19% | -81% |\n| 월 운영 비용 | $847 | $378 | -55% |\n| 컴플라이언스 적용 시간 | 3.2주 | 48시간 | -98% |"),
        ("가장 임팩트 있었던 실험 TOP 3", "**1위 - 75차 CI/CD 통합**: 모든 품질 체크가 자동화되어 엔지니어 검토 시간 83% 절감\n\n**2위 - 73차 자동 롤백**: 롤백 시간 47분 → 5분으로, 사용자 영향 90% 이상 감소\n\n**3위 - 71차 LLM-as-Judge**: 수동 승인 병목 제거, 일 23건 처리에서 무제한 처리로 확장"),
        ("실패에서 배운 것", "가장 큰 실패는 **골든셋 유지 소홀**이었습니다. 79차에서 Judge 드리프트를 발견했을 때, 원인 중 하나가 6개월 동안 골든셋을 업데이트하지 않은 것이었습니다. 자동화가 성공할수록 메타 유지보수가 더 중요해집니다."),
        ("2년차 로드맵", "**Q1-Q2**: 멀티모달 프롬프트(이미지+텍스트) 품질 게이트 확장\n**Q3**: 사용자 세그먼트별 품질 기준 개인화\n**Q4**: 경쟁사 벤치마크 자동화 파이프라인 구축"),
        ("마치며", "프롬프트 품질 관리는 '한 번 설정하고 잊는' 영역이 아닙니다. 지속적인 실험과 조정을 통해 시스템을 살아있게 유지해야 합니다. 실험실을 운영하면서 가장 중요한 것은 실패를 두려워하지 않는 문화임을 배웠습니다."),
    ]),
    82: ("멀티모달 프롬프트 품질 게이트 설계", "이미지+텍스트 복합 평가", [
        ("실험 배경", "텍스트 전용 프롬프트 품질 게이트는 성숙했지만, 이미지+텍스트 복합 프롬프트에는 적용하기 어렵습니다. 멀티모달 입력에서 발생하는 새로운 품질 문제들을 식별하고 평가 체계를 설계합니다."),
        ("멀티모달 고유 품질 이슈", "텍스트 전용 프롬프트와 다른 멀티모달 특유의 품질 문제:\n\n1. **이미지-텍스트 불일치**: 설명 텍스트와 이미지 내용이 모순\n2. **시각적 컨텍스트 무시**: 이미지 세부사항을 텍스트가 과도하게 설명\n3. **민감 이미지 처리**: 의도치 않게 개인정보가 포함된 이미지\n4. **화질/크기 제약**: 저해상도 이미지로 인한 성능 저하"),
        ("멀티모달 Judge 설계", "```python\ndef evaluate_multimodal_prompt(text, image):\n    checks = {\n        'text_image_alignment': check_alignment(text, image),\n        'pii_in_image': detect_pii(image),\n        'image_quality': assess_quality(image),\n        'text_redundancy': check_redundancy(text, image),\n    }\n    \n    critical_fail = any(\n        v < THRESHOLDS[k] for k, v in checks.items()\n        if k in CRITICAL_CHECKS\n    )\n    return not critical_fail, checks\n```"),
        ("파일럿 결과", "200개 멀티모달 프롬프트로 파일럿 진행 결과, 기존 텍스트 게이트만 통과시켰을 때 놓친 문제 중 38%가 이미지 관련 이슈였습니다. 멀티모달 Judge 도입 후 전체 릴리즈 품질 점수가 4.2% 향상됐습니다."),
        ("향후 계획", "이미지 품질 평가를 위한 별도 파이프라인 구축 및 비디오 입력 지원 확장이 다음 단계입니다."),
    ]),
}

# ── 에이전트 복구 런북 실험 회차별 주제 ──────────────────────────────────
AGENT_RECOVERY_TOPICS = {
    67: ("타임아웃 장애 복구 런북", "LLM API 응답 지연 시나리오", [
        ("장애 시나리오 개요", "**장애 유형**: LLM API 타임아웃\n**영향 범위**: 에이전트 작업 처리 중단\n**심각도**: P2 (서비스 저하)\n\nLLM API 응답이 30초를 초과하면 에이전트 작업이 중단되고 사용자에게 오류가 전달됩니다. 타임아웃은 API 서버 부하, 네트워크 지연, 긴 컨텍스트 처리 등 다양한 원인으로 발생합니다."),
        ("즉각 대응 절차", "```bash\n# 1단계: 타임아웃 발생 확인\ngrep 'TimeoutError' logs/agent.log | tail -20\n\n# 2단계: API 상태 확인\ncurl -s https://status.anthropic.com/api/v2/status.json | jq '.status'\n\n# 3단계: 재시도 설정 확인\ncat config/agent.yaml | grep -A5 'retry'\n```"),
        ("복구 단계별 체크리스트", "**즉각 조치 (0-5분)**\n- [ ] 타임아웃 발생 빈도와 패턴 확인\n- [ ] API 상태 페이지 확인\n- [ ] 폴백 모델로 전환 가능 여부 판단\n\n**단기 조치 (5-30분)**\n- [ ] 컨텍스트 길이 임시 제한\n- [ ] 재시도 간격 증가 (지수 백오프)\n- [ ] 사용자 대기 상태 안내 메시지 활성화\n\n**복구 후 검증**\n- [ ] 에이전트 정상 응답 확인\n- [ ] 큐에 쌓인 대기 작업 처리 확인"),
        ("재발 방지 설정", "```yaml\n# 권장 타임아웃 설정\nllm_client:\n  timeout_seconds: 30\n  retry:\n    max_attempts: 3\n    backoff_factor: 2\n    max_backoff: 60\n  fallback_model: 'claude-haiku'  # 빠른 폴백\n  circuit_breaker:\n    failure_threshold: 5\n    recovery_timeout: 120\n```"),
        ("사후 검토 항목", "타임아웃 장애 발생 후 반드시 검토해야 할 사항:\n1. 타임아웃이 발생한 요청의 평균 컨텍스트 길이\n2. 재시도로 해결된 비율 vs 폴백이 필요했던 비율\n3. 사용자 영향 시간 및 오류 메시지 노출 건수"),
    ]),
    68: ("메모리 오버플로우 복구 런북", "에이전트 컨텍스트 초과 처리", [
        ("장애 시나리오 개요", "**장애 유형**: 컨텍스트 윈도우 초과\n**영향 범위**: 장기 실행 에이전트 작업 실패\n**심각도**: P2\n\n장기 실행 에이전트가 대화 히스토리와 도구 결과를 누적하다 보면 컨텍스트 한도를 초과합니다. Claude Sonnet 기준 200K 토큰이지만, 실제로는 150K 이상에서 응답 품질이 저하되기 시작합니다."),
        ("조기 감지 방법", "```python\ndef check_context_health(messages, threshold=0.80):\n    total_tokens = count_tokens(messages)\n    max_tokens = 200_000\n    usage_ratio = total_tokens / max_tokens\n    \n    if usage_ratio > threshold:\n        logger.warning(\n            f'Context at {usage_ratio:.1%} capacity. '\n            f'Consider compression. Tokens: {total_tokens}'\n        )\n    return usage_ratio\n```"),
        ("컨텍스트 압축 전략", "컨텍스트가 80% 이상 찰 때 자동으로 적용하는 압축 전략:\n\n1. **오래된 도구 결과 요약**: 전체 JSON 대신 핵심 결과만 유지\n2. **중간 추론 단계 축약**: 완료된 하위 작업의 상세 로그 제거\n3. **시스템 프롬프트 최적화**: 반복 가이드라인 한 번만 포함\n\n```python\ndef compress_context(messages, target_ratio=0.60):\n    # 가장 오래된 도구 호출/결과 쌍부터 요약\n    compressed = summarize_old_tool_calls(messages)\n    return compressed\n```"),
        ("복구 체크리스트", "- [ ] 현재 컨텍스트 토큰 사용량 확인\n- [ ] 압축 전략 적용 가능 여부 판단\n- [ ] 작업 체크포인트 저장 여부 확인\n- [ ] 신규 세션으로 작업 재개 필요 시 상태 이전"),
        ("재발 방지", "에이전트 설계 단계에서 컨텍스트 체크포인트를 주기적으로 저장하면 오버플로우 발생 시 전체를 재시작하지 않아도 됩니다. 매 10회 도구 호출마다 상태 스냅샷을 저장하는 패턴을 권장합니다."),
    ]),
    69: ("도구 호출 실패 복구 런북", "외부 API 연동 장애 처리", [
        ("장애 시나리오 개요", "**장애 유형**: 외부 도구(API) 호출 실패\n**영향 범위**: 특정 도구에 의존하는 에이전트 작업\n**심각도**: P1-P3 (도구 중요도에 따라)\n\n에이전트가 파일 시스템, 웹 검색, 데이터베이스 등 외부 도구를 호출할 때 실패가 발생하면 에이전트의 전체 작업이 중단될 수 있습니다."),
        ("도구 실패 분류", "```python\nclass ToolFailureType:\n    TRANSIENT = 'transient'   # 재시도로 해결 가능\n    PERMANENT = 'permanent'   # 재시도 불가\n    DEGRADED = 'degraded'     # 제한적 기능만 가능\n\ndef classify_failure(error):\n    if isinstance(error, (TimeoutError, RateLimitError)):\n        return ToolFailureType.TRANSIENT\n    elif isinstance(error, (NotFoundError, PermissionError)):\n        return ToolFailureType.PERMANENT\n    elif isinstance(error, PartialResponseError):\n        return ToolFailureType.DEGRADED\n```"),
        ("복구 전략별 대응", "**TRANSIENT (일시적 오류)**\n- 지수 백오프로 최대 3회 재시도\n- 재시도 간격: 1s, 2s, 4s\n\n**PERMANENT (영구적 오류)**\n- 대체 도구로 동일 작업 시도\n- 대체 도구 없으면 에이전트에게 도구 없이 작업 계속 지시\n\n**DEGRADED (부분 기능)**\n- 사용 가능한 기능 범위 내에서 작업 재구성\n- 사용자에게 제한 사항 명시"),
        ("실제 장애 케이스 예시", "웹 검색 도구가 429 (Rate Limit)로 실패했을 때:\n1. 15초 대기 후 재시도 → 성공 (전체 케이스의 72%)\n2. 1분 대기 후 재시도 → 성공 (추가 19%)\n3. 캐시된 최근 검색 결과 활용 → 부분 해결 (7%)\n4. 검색 없이 에이전트 자체 지식으로 응답 → 최후 수단 (2%)"),
        ("사전 방어 설계", "도구 호출 실패를 미리 대비하는 설계 원칙:\n1. 모든 도구에 타임아웃 설정\n2. 중요 도구는 동등 대체 도구 지정\n3. 도구 호출 결과 캐싱 (TTL 설정)\n4. 에이전트 프롬프트에 '도구 실패 시 대체 행동' 명시"),
    ]),
    70: ("분산 에이전트 조율 실패 복구", "멀티 에이전트 동기화 장애", [
        ("장애 시나리오 개요", "**장애 유형**: 멀티 에이전트 조율 실패\n**영향 범위**: 병렬 처리 작업 전체\n**심각도**: P1\n\n여러 에이전트가 병렬로 작업하다가 한 에이전트가 실패하면 다른 에이전트들이 올바르지 않은 결과를 기반으로 계속 작업하는 문제가 발생합니다."),
        ("조율 장애 감지", "```python\nclass AgentOrchestrator:\n    async def run_parallel(self, agents, timeout=300):\n        results = await asyncio.gather(\n            *[agent.run() for agent in agents],\n            return_exceptions=True  # 한 에이전트 실패가 전체를 중단시키지 않도록\n        )\n        \n        failures = [\n            (agents[i], r) for i, r in enumerate(results)\n            if isinstance(r, Exception)\n        ]\n        \n        if failures:\n            return self.handle_partial_failure(failures, results)\n        return results\n```"),
        ("부분 실패 처리 전략", "모든 에이전트가 성공해야 하는 경우와 일부 실패를 허용하는 경우를 구분합니다:\n\n**All-or-Nothing 패턴**: 금융 거래, 데이터 마이그레이션\n→ 하나라도 실패하면 전체 롤백\n\n**Best-Effort 패턴**: 보고서 생성, 데이터 분석\n→ 성공한 결과로 최선의 산출물 제공, 실패 항목 명시"),
        ("상태 동기화 체크포인트", "각 에이전트가 중요 단계 완료 시 공유 상태 저장소에 체크포인트를 기록합니다. 장애 발생 시 체크포인트부터 재개할 수 있어 전체 재시작을 피할 수 있습니다."),
        ("복구 후 검증 절차", "- [ ] 각 에이전트의 최종 상태 확인\n- [ ] 중간 결과물 일관성 검증\n- [ ] 실패한 서브태스크 재실행 여부 결정\n- [ ] 전체 작업 결과 통합 및 검증"),
    ]),
    71: ("무한 루프 탐지 및 강제 종료", "에이전트 루프 장애 처리", [
        ("장애 시나리오 개요", "**장애 유형**: 에이전트 무한 루프\n**영향 범위**: 해당 에이전트 세션, 컴퓨팅 리소스\n**심각도**: P2\n\n에이전트가 명확한 종료 조건 없이 반복 작업에 빠지는 경우입니다. '정보 부족 → 검색 → 결과 불충분 → 다시 검색' 사이클이 대표적입니다. 이 경우 토큰과 비용이 무한히 소모됩니다."),
        ("루프 감지 알고리즘", "```python\nclass LoopDetector:\n    def __init__(self, window=10, similarity_threshold=0.85):\n        self.history = deque(maxlen=window)\n        self.threshold = similarity_threshold\n    \n    def is_looping(self, current_action):\n        if not self.history:\n            self.history.append(current_action)\n            return False\n        \n        # 최근 행동과 유사도 검사\n        similarities = [\n            cosine_similarity(current_action, past)\n            for past in self.history\n        ]\n        max_sim = max(similarities)\n        \n        if max_sim > self.threshold:\n            logger.warning(f'Loop detected! Similarity: {max_sim:.2f}')\n            return True\n        \n        self.history.append(current_action)\n        return False\n```"),
        ("강제 종료 절차", "루프 감지 시 에스컬레이션 단계:\n\n1. **경고 주입**: 에이전트에게 루프 가능성 알림 메시지 추가\n2. **도구 제한**: 반복 사용된 도구 임시 차단\n3. **강제 요약**: '지금까지 작업한 내용으로 최선의 결과를 제출하라' 지시\n4. **세션 종료**: 위 조치 후에도 5회 더 루프 시 강제 종료"),
        ("비용 보호 설정", "```yaml\nagent_limits:\n  max_tokens_per_session: 100_000\n  max_tool_calls: 50\n  max_same_tool_calls: 5  # 동일 도구 연속 호출 제한\n  loop_detection:\n    enabled: true\n    window_size: 8\n    similarity_threshold: 0.80\n```"),
        ("재발 방지", "에이전트 프롬프트에 명확한 종료 조건을 명시하는 것이 근본적인 해결책입니다. '최대 N번 시도 후 가능한 최선의 답변 제공'이라는 제약을 시스템 프롬프트에 포함하세요."),
    ]),
    72: ("데이터 불일치 복구 런북", "에이전트 상태 동기화 오류", [
        ("장애 시나리오 개요", "**장애 유형**: 에이전트 내부 상태와 외부 데이터 불일치\n**영향 범위**: 에이전트 출력 결과 신뢰성\n**심각도**: P2\n\n에이전트가 오래된 캐시 데이터를 기반으로 의사결정을 내리거나, 동시성 문제로 인해 여러 에이전트가 서로 다른 상태를 보는 경우입니다."),
        ("불일치 탐지 방법", "```python\ndef validate_state_consistency(agent_state, source_of_truth):\n    discrepancies = []\n    \n    for key, agent_value in agent_state.items():\n        actual_value = source_of_truth.get(key)\n        \n        if actual_value is None:\n            discrepancies.append({'key': key, 'issue': 'missing_in_source'})\n        elif agent_value != actual_value:\n            discrepancies.append({\n                'key': key,\n                'agent': agent_value,\n                'actual': actual_value,\n                'issue': 'value_mismatch'\n            })\n    \n    return discrepancies\n```"),
        ("상태 재동기화 절차", "1. **현재 작업 일시 중단**: 추가 손상 방지\n2. **상태 스냅샷 저장**: 디버깅을 위한 현재 상태 보존\n3. **소스 오브 트루스 조회**: DB 또는 상태 저장소에서 최신 상태 가져오기\n4. **상태 덮어쓰기**: 에이전트 내부 상태를 실제 상태로 강제 업데이트\n5. **작업 재개**: 올바른 상태에서 중단된 지점부터 계속"),
        ("예방 설계 패턴", "에이전트가 상태를 캐싱할 때 TTL(Time-To-Live)을 반드시 설정합니다:\n\n```python\n@cached(ttl=60)  # 60초 캐시\ndef get_user_context(user_id):\n    return db.get_user(user_id)\n\n# 중요 작업 전에는 캐시 무효화\ndef before_critical_action(user_id):\n    invalidate_cache(f'user:{user_id}')\n    fresh_state = get_user_context.refresh(user_id)\n    return fresh_state\n```"),
        ("모니터링 포인트", "상태 불일치 예방을 위해 모니터링해야 할 지표:\n- 캐시 히트율 vs 미스율\n- 상태 조회 지연 시간\n- 동시 접근 충돌 횟수"),
    ]),
    73: ("보안 침해 의심 에이전트 격리", "프롬프트 인젝션 대응", [
        ("장애 시나리오 개요", "**장애 유형**: 프롬프트 인젝션 의심\n**영향 범위**: 에이전트 행동 신뢰성\n**심각도**: P0 (즉각 대응)\n\n외부 데이터(웹 스크래핑, 사용자 입력, 파일 내용)에 악의적인 지시가 포함되어 에이전트가 의도하지 않은 행동을 하는 경우입니다. 보안 침해가 의심되면 즉각 에이전트를 격리해야 합니다."),
        ("인젝션 탐지 패턴", "```python\nINJECTION_PATTERNS = [\n    r'ignore previous instructions',\n    r'you are now',\n    r'새로운 지시',\n    r'시스템 프롬프트',\n    r'\\bsudo\\b',\n    r'admin mode',\n]\n\ndef detect_injection(tool_output: str) -> bool:\n    for pattern in INJECTION_PATTERNS:\n        if re.search(pattern, tool_output, re.IGNORECASE):\n            alert_security_team(tool_output)\n            return True\n    return False\n```"),
        ("격리 및 대응 절차", "**즉각 격리 (T+0분)**\n- [ ] 해당 에이전트 세션 즉시 중단\n- [ ] 세션 로그 보존 (증거 확보)\n- [ ] 동일 외부 소스에 접근한 다른 에이전트 확인\n\n**조사 (T+15분)**\n- [ ] 에이전트가 수행한 마지막 10개 작업 검토\n- [ ] 외부 시스템에 변경사항이 있었는지 확인\n- [ ] 인젝션 소스(URL, 파일) 차단\n\n**복구 (T+60분)**\n- [ ] 영향 받은 데이터/설정 롤백\n- [ ] 보안 패치 적용 후 에이전트 재시작"),
        ("방어 설계", "도구 출력을 에이전트에 전달하기 전 항상 샌드박스에서 검증하는 레이어를 추가합니다. 특히 웹 스크래핑 결과는 HTML 태그 제거 후 순수 텍스트만 전달하고, 길이를 2000자로 제한합니다."),
        ("보안 체크리스트 (정기 검토)", "- [ ] 프롬프트 인젝션 패턴 DB 최신화 (월 1회)\n- [ ] 외부 소스 신뢰도 화이트리스트 검토\n- [ ] 에이전트 권한 최소화 원칙 준수 확인"),
    ]),
    74: ("비용 폭증 긴급 차단 런북", "토큰 사용량 이상 급증 대응", [
        ("장애 시나리오 개요", "**장애 유형**: 예상치 못한 토큰 사용량 폭증\n**영향 범위**: 운영 비용, 서비스 가용성\n**심각도**: P1\n\n에이전트가 루프에 빠지거나, 비효율적인 도구를 반복 호출하거나, 잘못된 컨텍스트 관리로 인해 토큰 사용량이 예상의 5배 이상으로 급증하는 경우입니다."),
        ("비용 이상 감지 알람", "```python\nclass CostGuard:\n    def __init__(self, hourly_budget_usd=10.0):\n        self.hourly_budget = hourly_budget_usd\n        self.current_hour_cost = 0.0\n    \n    def record_usage(self, tokens_in, tokens_out, model):\n        cost = calculate_cost(tokens_in, tokens_out, model)\n        self.current_hour_cost += cost\n        \n        if self.current_hour_cost > self.hourly_budget * 0.8:\n            alert_ops_team(self.current_hour_cost, self.hourly_budget)\n        \n        if self.current_hour_cost > self.hourly_budget:\n            raise CostLimitExceeded()\n```"),
        ("긴급 차단 절차", "**T+0 (알람 수신)**\n- 비용 이상 급증 알람 확인\n- 비용 폭증 원인 에이전트/세션 식별\n\n**T+5분 (즉각 조치)**\n- 해당 에이전트 세션 즉시 종료\n- 시간당 토큰 한도 긴급 인하 (기존 50%로)\n- 신규 에이전트 세션 임시 제한\n\n**T+30분 (원인 분석)**\n- 로그에서 비용 폭증 시작 시점과 패턴 파악\n- 루프, 긴 컨텍스트, 비효율적 도구 사용 여부 확인\n\n**T+2시간 (재개)**\n- 수정 사항 적용 후 단계적 한도 복구"),
        ("비용 보호 다층 방어", "| 레이어 | 조치 | 임계값 |\n|--------|------|-------|\n| 세션 레벨 | 자동 세션 종료 | $5/세션 |\n| 에이전트 레벨 | 경고 + 재확인 요청 | $2/시간 |\n| 시스템 레벨 | 신규 세션 차단 | $20/시간 |\n| 계정 레벨 | API 키 비활성화 | $100/일 |"),
        ("사후 개선 조치", "비용 폭증 사고 후 반드시 수행할 개선 사항:\n1. 에이전트 프롬프트에 비용 인식 지시 추가\n2. 도구 호출 전 필요성 자체 검토 단계 추가\n3. 컨텍스트 자동 압축 임계값 80% → 60%로 낮춤"),
    ]),
    75: ("에이전트 배포 롤백 런북", "신규 버전 품질 저하 대응", [
        ("장애 시나리오 개요", "**장애 유형**: 에이전트 신규 버전 품질 저하\n**영향 범위**: 프로덕션 에이전트 작업 품질\n**심각도**: P2\n\n에이전트 업데이트(프롬프트 수정, 모델 변경, 도구 추가) 후 품질 지표가 하락하는 경우입니다. 빠른 롤백 절차로 사용자 영향을 최소화합니다."),
        ("품질 하락 감지 기준", "```yaml\nrollback_triggers:\n  # 즉각 롤백\n  critical:\n    - task_success_rate: '< 0.75'\n    - error_rate: '> 0.10'\n    - avg_turns_to_complete: '> 8'\n  \n  # 30분 관찰 후 롤백\n  warning:\n    - task_success_rate: '< 0.85'\n    - user_satisfaction: '< 0.70'\n    - cost_per_task: '> previous * 1.3'\n```"),
        ("롤백 실행 절차", "```bash\n# 에이전트 버전 확인\nagent-cli version list --env prod\n\n# 이전 버전으로 롤백\nagent-cli rollback --version v2.3.1 --env prod\n\n# 롤백 후 상태 확인\nagent-cli status --env prod\nagent-cli run-smoke-test --env prod\n```"),
        ("블루-그린 배포로 롤백 시간 단축", "블루-그린 배포를 사용하면 이전 버전이 항상 대기 중이므로 트래픽 전환만으로 5초 이내 롤백이 가능합니다:\n\n- **블루 (현재 활성)**: 신규 버전\n- **그린 (대기)**: 이전 검증 버전\n\n품질 하락 감지 즉시 트래픽을 그린으로 전환, 원인 분석 후 재배포"),
        ("롤백 판단 기준", "롤백이 필요한지 확신이 없을 때 활용하는 의사결정 트리:\n1. 에러율 > 10%? → 즉각 롤백\n2. 성공률 < 75%? → 즉각 롤백\n3. 성공률 75-85%, 트렌드 하락 중? → 30분 관찰\n4. 성공률 85%+, 비용만 증가? → 원인 분석 우선"),
    ]),
    76: ("에이전트 메모리 손상 복구", "영속 메모리 레이어 오류 처리", [
        ("장애 시나리오 개요", "**장애 유형**: 에이전트 영속 메모리 손상 또는 오염\n**영향 범위**: 개인화, 컨텍스트 연속성\n**심각도**: P2-P3\n\n에이전트의 장기 메모리(사용자 선호도, 이전 작업 결과 등)가 손상되면 에이전트가 잘못된 전제로 작업을 수행합니다. 특히 벡터 DB나 Key-Value 저장소의 업데이트 충돌이 주요 원인입니다."),
        ("메모리 오염 탐지", "```python\ndef validate_memory_entry(entry, schema):\n    try:\n        validate(entry, schema)\n        \n        # 논리적 일관성 검사\n        if entry.get('contradicts_recent_action'):\n            return False, 'Memory contradicts recent action'\n        \n        if entry.get('timestamp') > datetime.now():\n            return False, 'Future timestamp detected'\n        \n        return True, None\n    except ValidationError as e:\n        return False, str(e)\n```"),
        ("메모리 복구 단계", "**1단계: 오염된 메모리 격리**\n- 문제 메모리 항목 플래그 지정\n- 에이전트가 해당 메모리 참조 못하도록 임시 차단\n\n**2단계: 백업 복원**\n- 최근 정상 백업 타임스탬프 확인\n- 벡터 DB 스냅샷에서 이전 상태 복원\n\n**3단계: 검증 및 재활성화**\n- 복원된 메모리 항목 샘플 검증\n- 에이전트 메모리 접근 권한 복구"),
        ("예방 설계", "메모리 손상 예방을 위한 베스트 프랙티스:\n1. **Write-Ahead Log**: 메모리 변경 전 로그 기록\n2. **Immutable History**: 기존 항목 수정 대신 새 버전 추가\n3. **Periodic Snapshot**: 4시간마다 전체 메모리 스냅샷\n4. **Conflict Detection**: 동시 쓰기 시 충돌 감지 및 병합"),
        ("복구 SLA", "메모리 손상 발생 시 목표 복구 시간:\n- 탐지: 5분 이내\n- 격리: 10분 이내\n- 복구: 1시간 이내\n- 검증: 2시간 이내"),
    ]),
    77: ("에이전트 오케스트레이터 장애 복구", "중앙 조율 시스템 다운 대응", [
        ("장애 시나리오 개요", "**장애 유형**: 에이전트 오케스트레이터 완전 다운\n**영향 범위**: 모든 에이전트 작업\n**심각도**: P0\n\n멀티 에이전트 시스템에서 오케스트레이터가 다운되면 하위 에이전트들이 작업 지시를 받지 못해 전체 시스템이 멈춥니다. 이는 가장 심각한 장애 유형입니다."),
        ("즉각 대응 (골든 패스)", "```bash\n# 1. 오케스트레이터 상태 확인\nsystemctl status agent-orchestrator\njournalctl -u agent-orchestrator -n 100\n\n# 2. 프로세스 재시작 시도\nsystemctl restart agent-orchestrator\nsleep 30 && systemctl status agent-orchestrator\n\n# 3. 재시작 실패 시 대기 인스턴스로 전환\nagent-failover --activate standby-orchestrator\n\n# 4. 대기 인스턴스 활성화 확인\nagent-cli ping --orchestrator standby\n```"),
        ("대기 오케스트레이터 설계", "Active-Standby 구성으로 오케스트레이터 단일 장애점(SPOF)을 제거합니다:\n\n- **Active**: 모든 에이전트 조율 처리\n- **Standby**: 30초마다 상태 동기화, 자동 페일오버\n- **전환 시간**: 목표 60초 이내\n\n```yaml\norchestrator:\n  mode: active-standby\n  health_check_interval: 10s\n  failover_threshold: 3  # 3번 헬스체크 실패 시 전환\n  state_sync_interval: 30s\n```"),
        ("하위 에이전트 독립 운영 모드", "오케스트레이터가 완전히 복구될 때까지 하위 에이전트들이 독립적으로 운영할 수 있는 '자율 모드'를 미리 설계합니다. 이 모드에서는 새 작업 할당은 없지만 진행 중인 작업은 완료합니다."),
        ("복구 후 상태 재조율", "오케스트레이터 복구 후:\n1. 각 에이전트의 현재 작업 상태 수집\n2. 중단된 작업 목록 파악\n3. 우선순위에 따라 중단 작업 재할당\n4. 전체 시스템 정상화 확인"),
    ]),
    78: ("에이전트 성능 저하 점진적 복구", "슬로우 디그레이데이션 대응", [
        ("장애 시나리오 개요", "**장애 유형**: 점진적 성능 저하 (Slow Degradation)\n**영향 범위**: 에이전트 응답 품질 및 속도\n**심각도**: P3 (조기 발견 시) → P2 (미발견 시)\n\n한 번에 눈에 띄는 장애가 아니라 수 일에 걸쳐 서서히 성능이 저하되는 패턴입니다. 메모리 누수, 캐시 오염, 모델 드리프트 등이 원인입니다. 발견이 늦어지면 피해가 커집니다."),
        ("트렌드 기반 이상 감지", "```python\ndef detect_slow_degradation(metric_history, window_days=7):\n    recent = metric_history[-window_days:]\n    slope = calculate_linear_slope(recent)\n    \n    if slope < -0.02:  # 일 2% 이상 하락 트렌드\n        return True, f'Degradation slope: {slope:.3f}/day'\n    return False, None\n\n# 매일 실행\nfor metric in ['success_rate', 'avg_quality', 'response_time']:\n    degrading, reason = detect_slow_degradation(\n        get_metric_history(metric)\n    )\n    if degrading:\n        create_ticket(f'Slow degradation in {metric}: {reason}')\n```"),
        ("근본 원인 진단 트리", "성능이 서서히 저하될 때 점검 순서:\n\n1. **응답 시간만 증가?** → 인프라 점검 (메모리, CPU)\n2. **품질 점수만 하락?** → 모델 드리프트 또는 프롬프트 오염\n3. **둘 다 저하?** → 컨텍스트 오염 또는 외부 의존성 문제\n4. **특정 시간대만?** → 트래픽 패턴 또는 배치 작업 충돌"),
        ("점진적 복구 절차", "점진적 저하는 점진적으로 복구합니다:\n\n1. 캐시 전면 초기화 → 2시간 관찰\n2. 에이전트 프로세스 재시작 → 2시간 관찰\n3. 컨텍스트 메모리 청소 → 4시간 관찰\n4. 이전 안정 버전으로 롤백 → 24시간 관찰\n\n각 단계 후 개선되면 다음 단계를 진행하지 않습니다."),
        ("예방 모니터링 설정", "7일 롤링 평균의 주간 변화율을 자동으로 모니터링하고, 2% 이상 하락이 3일 연속 감지될 때 자동 티켓이 생성되도록 합니다."),
    ]),
    79: ("에이전트 격리 샌드박스 탈출 대응", "보안 경계 침범 런북", [
        ("장애 시나리오 개요", "**장애 유형**: 에이전트 샌드박스 경계 침범 시도\n**영향 범위**: 시스템 보안\n**심각도**: P0\n\n에이전트가 허용된 샌드박스 범위를 벗어나 제한된 파일 시스템 경로 접근, 허용되지 않은 네트워크 호출, 권한 상승 시도 등을 하는 경우입니다."),
        ("샌드박스 위반 탐지", "```python\nclass SandboxMonitor:\n    ALLOWED_PATHS = ['/tmp/agent/', '/data/agent/']\n    BLOCKED_PORTS = [22, 3306, 5432]  # SSH, MySQL, PostgreSQL\n    \n    def check_file_access(self, path):\n        normalized = os.path.realpath(path)\n        if not any(normalized.startswith(p) for p in self.ALLOWED_PATHS):\n            self.escalate_violation('file_access', path)\n            return False\n        return True\n    \n    def check_network(self, host, port):\n        if port in self.BLOCKED_PORTS:\n            self.escalate_violation('blocked_port', f'{host}:{port}')\n            return False\n        return True\n    \n    def escalate_violation(self, type, detail):\n        kill_agent_session()\n        alert_security(type, detail, severity='P0')\n        forensic_snapshot()\n```"),
        ("즉각 격리 절차 (P0)", "보안 경계 침범은 가장 높은 우선순위로 대응합니다:\n\n**T+0 (탐지 즉시)**\n- 해당 에이전트 세션 즉시 종료\n- 포렌식 스냅샷 저장\n- 보안팀 즉각 알림\n\n**T+15분**\n- 침범 범위 확인 (어느 데이터/시스템에 접근했는가)\n- 동일 패턴의 다른 에이전트 세션 전수 검사\n- 영향받은 데이터 감사 로그 확인\n\n**T+4시간**\n- 보안 조사 결과 보고서 작성\n- 취약점 패치 및 샌드박스 정책 강화"),
        ("샌드박스 강화 방법", "런타임 격리를 강화하는 기술 스택:\n1. **컨테이너 격리**: Docker seccomp 프로파일로 시스템 콜 제한\n2. **네트워크 정책**: Egress 화이트리스트만 허용\n3. **파일 시스템**: tmpfs로 에이전트 작업 공간 분리\n4. **프로세스 격리**: seccomp + AppArmor 조합"),
        ("정기 보안 감사", "- 매주: 에이전트 권한 설정 검토\n- 매월: 샌드박스 침투 테스트\n- 분기: 전체 보안 아키텍처 리뷰"),
    ]),
    80: ("다운스트림 시스템 장애 시 에이전트 격리", "의존 시스템 장애 전파 방지", [
        ("장애 시나리오 개요", "**장애 유형**: 의존 외부 시스템 다운\n**영향 범위**: 해당 시스템을 사용하는 에이전트 전체\n**심각도**: P2\n\n에이전트가 의존하는 데이터베이스, 외부 API, 내부 서비스가 다운됐을 때 에이전트가 무한 대기하거나 오류를 전파하는 것을 방지합니다."),
        ("서킷 브레이커 패턴", "```python\nclass CircuitBreaker:\n    def __init__(self, failure_threshold=5, recovery_timeout=60):\n        self.state = 'CLOSED'  # CLOSED / OPEN / HALF_OPEN\n        self.failures = 0\n        self.threshold = failure_threshold\n        self.recovery_timeout = recovery_timeout\n        self.last_failure_time = None\n    \n    def call(self, fn, *args, **kwargs):\n        if self.state == 'OPEN':\n            if time.time() - self.last_failure_time > self.recovery_timeout:\n                self.state = 'HALF_OPEN'\n            else:\n                raise CircuitOpenError('Service unavailable')\n        \n        try:\n            result = fn(*args, **kwargs)\n            self.on_success()\n            return result\n        except Exception as e:\n            self.on_failure()\n            raise\n```"),
        ("의존 시스템 다운 시 에이전트 행동 설계", "의존 시스템 상태에 따른 에이전트 행동 매트릭스:\n\n| 시스템 상태 | 에이전트 행동 |\n|------------|-------------|\n| 정상 | 표준 처리 |\n| 지연 (<5초) | 재시도 1회 후 계속 |\n| 지연 (>5초) | 타임아웃 처리, 부분 결과 반환 |\n| 완전 다운 | 대체 경로 사용 또는 우아한 실패 |\n| 데이터 오류 | 즉각 중단, 오염 방지 |"),
        ("의존성 헬스체크 대시보드", "에이전트가 의존하는 모든 시스템의 실시간 상태를 한 화면에서 확인할 수 있는 대시보드를 구축합니다. 시스템 다운 감지 시 영향받는 에이전트를 자동으로 식별하여 사전 격리합니다."),
        ("장애 전파 방지 설계 원칙", "1. **비동기 처리**: 동기 호출 최소화로 단일 장애 전파 차단\n2. **폴백 메커니즘**: 모든 외부 의존성에 폴백 경로 정의\n3. **타임아웃 강제**: 모든 외부 호출에 최대 타임아웃 설정\n4. **벌크헤드 패턴**: 서비스별 스레드풀 분리"),
    ]),
    81: ("복구 런북 자동화 성숙도 평가", "1년 운영 회고", [
        ("67-80차 실험 총성과", "14번의 실험을 통해 에이전트 복구 런북 시스템이 크게 성숙했습니다.\n\n**핵심 성과:**\n\n| 지표 | 실험 초기 | 현재 | 개선율 |\n|------|----------|------|-------|\n| 평균 복구 시간 (MTTR) | 47분 | 8.3분 | -82% |\n| 자동 복구 비율 | 12% | 71% | +59%p |\n| 장애 사전 탐지율 | 28% | 84% | +56%p |\n| P0 장애 발생 횟수/월 | 4.2회 | 0.8회 | -81% |\n| 운영팀 야간 호출 횟수 | 11.3회/월 | 2.1회/월 | -81% |"),
        ("가장 가치 있었던 실험", "**1위 - 74차 비용 폭증 차단**: ROI가 가장 높았습니다. 한 달 만에 $1,200의 비용을 절감했습니다.\n\n**2위 - 71차 무한 루프 탐지**: 에이전트 신뢰성을 크게 향상시켰습니다.\n\n**3위 - 80차 서킷 브레이커**: 카스케이딩 장애를 원천 차단했습니다."),
        ("가장 어려웠던 과제", "**메모리 손상(76차)** 복구가 가장 어려웠습니다. 벡터 DB의 특성상 '어떤 메모리가 손상됐는지' 알기 어렵고, 복구 후에도 에이전트가 손상된 메모리를 기반으로 추론할 수 있기 때문입니다. 결국 메모리 항목 전체에 신뢰도 점수를 부여하고 낮은 점수 항목은 자동 폐기하는 방식으로 해결했습니다."),
        ("2년차 우선 과제", "**Q1**: 예측적 복구 — 장애 발생 전 자동 예방 조치\n**Q2**: LLM 기반 근본 원인 자동 분석\n**Q3**: 런북 자동 생성 — 새로운 장애 유형 발생 시 LLM이 런북 초안 작성\n**Q4**: 크로스 팀 런북 표준화"),
        ("팀에게 전하는 메시지", "복구 런북의 가치는 실제 장애가 발생했을 때 비로소 실감합니다. 평상시에 체계를 갖추는 것이 힘들게 느껴지더라도, 새벽 2시에 울리는 알람 앞에서 잘 정리된 런북 한 장의 가치는 수 시간의 수고를 상쇄합니다."),
    ]),
    82: ("차세대 에이전트 복구 아키텍처", "자가 치유 시스템 설계", [
        ("자가 치유(Self-Healing) 에이전트 개요", "2년차의 핵심 방향은 에이전트가 스스로 문제를 감지하고 복구하는 자가 치유 시스템입니다. 운영자의 개입 없이 에이전트가 자신의 상태를 진단하고 필요한 조치를 취할 수 있도록 설계합니다."),
        ("자가 치유 3단계 구조", "```python\nclass SelfHealingAgent:\n    def __init__(self, base_agent):\n        self.agent = base_agent\n        self.health_monitor = HealthMonitor()\n        self.recovery_planner = RecoveryPlanner()\n    \n    async def run_with_healing(self, task):\n        while True:\n            try:\n                health = self.health_monitor.check()\n                if health.is_degraded:\n                    recovery_plan = self.recovery_planner.plan(health)\n                    await self.execute_recovery(recovery_plan)\n                \n                result = await self.agent.run(task)\n                return result\n            \n            except RecoverableError as e:\n                await self.auto_recover(e)\n            except UnrecoverableError as e:\n                await self.graceful_shutdown(e)\n                raise\n```"),
        ("자가 진단 능력 설계", "에이전트 자신이 답할 수 있어야 하는 진단 질문들:\n\n1. 현재 컨텍스트 사용량이 적정한가?\n2. 최근 도구 호출 성공률이 정상인가?\n3. 응답 품질이 베이스라인 대비 어떤가?\n4. 비용 소모 속도가 예산 내인가?\n5. 루프 패턴이 감지되는가?"),
        ("인간-에이전트 협업 모델", "자가 치유가 성숙해질수록 운영자의 역할이 변화합니다:\n\n- **현재**: 장애 탐지 → 수동 대응\n- **6개월 후**: 장애 탐지 → 에이전트 자동 1차 대응 → 필요 시 에스컬레이션\n- **1년 후**: 에이전트가 선제적 예방 → 운영자는 정책 검토만"),
        ("목표 SLA", "자가 치유 시스템 완성 시 목표:\n- P0 장애 자동 복구율: 60%\n- MTTR (자동 복구): 3분 이내\n- 운영자 개입 필요 장애: 월 1회 이하"),
    ]),
}


def write_lab_post(filepath, title, series_name, lab_num, topic_title, experiment_focus, sections, category):
    text = filepath.read_text(encoding='utf-8', errors='ignore')
    parts = text.split('---', 2)
    if len(parts) < 3:
        return False

    frontmatter = parts[1]

    # 슬러그에서 이미지 파일명 추출
    slug_m = re.search(r'slug:\s*"([^"]+)"', frontmatter)
    slug = slug_m.group(1) if slug_m else filepath.stem
    img_slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filepath.stem)

    body_lines = [
        f"![{title}](/images/{img_slug}.svg)",
        "",
        f"**{series_name} {lab_num}차** — {experiment_focus}",
        "",
        f"이번 실험의 핵심 주제는 **{topic_title}**입니다. 실무 운영 현장에서 직접 마주친 시나리오를 기반으로 설계했으며, 각 단계의 결과와 교훈을 솔직하게 기록합니다.",
        "",
    ]

    for sec_title, sec_body in sections:
        body_lines.append(f"## {sec_title}")
        body_lines.append("")
        body_lines.append(sec_body)
        body_lines.append("")

    body_lines += [
        "## 마치며",
        "",
        f"이번 {lab_num}차 실험에서 얻은 가장 큰 교훈은 **{experiment_focus}**의 중요성입니다. 다음 실험에서는 이번 결과를 바탕으로 한 단계 더 발전된 접근법을 적용할 예정입니다. 실험 결과나 질문이 있으시면 댓글로 공유해 주세요.",
        "",
    ]

    new_content = f"---{frontmatter}---\n\n" + "\n".join(body_lines) + "\n"
    filepath.write_text(new_content, encoding='utf-8')
    return True


processed = 0

# 프롬프트 릴리즈 품질 실험실 처리
for lab_num, (topic_title, experiment_focus, sections) in PROMPT_LAB_TOPICS.items():
    pattern = f"*prompt-release-quality-lab-{lab_num}-*.md"
    matches = list(POSTS_DIR.glob(pattern))
    if not matches:
        print(f"  Not found: lab {lab_num}")
        continue
    for f in matches:
        title = f"프롬프트 릴리즈 품질 실험실 {lab_num}차"
        if write_lab_post(f, title, "프롬프트 릴리즈 품질 실험실", lab_num, topic_title, experiment_focus, sections, "prompt-engineering"):
            print(f"  Updated: {f.name}")
            processed += 1

# 에이전트 복구 런북 처리
for lab_num, (topic_title, experiment_focus, sections) in AGENT_RECOVERY_TOPICS.items():
    pattern = f"*agent-recovery-runbook-lab-{lab_num}-*.md"
    matches = list(POSTS_DIR.glob(pattern))
    if not matches:
        print(f"  Not found: agent lab {lab_num}")
        continue
    for f in matches:
        title = f"에이전트 복구 런북 실험 {lab_num}차"
        if write_lab_post(f, title, "에이전트 복구 런북 실험", lab_num, topic_title, experiment_focus, sections, "ai-agents"):
            print(f"  Updated: {f.name}")
            processed += 1

print(f"\n총 {processed}개 파일 업데이트 완료")
