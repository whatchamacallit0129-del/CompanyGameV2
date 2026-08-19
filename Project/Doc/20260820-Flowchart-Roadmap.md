# 2026-08-20 — CompanyGameV2 개발 플로우 / 로드맵

## 확정 플로우

```text
사용자
  ↓
ChatGPT
  ↓
GitHub
  ↓
GitHub Actions
  ↓
Cline CLI
  ↓
Unity
```

## 핵심 방향
- 기존 CompanyGameAgent / Bridge / Agent Queue 구조는 폐기.
- MCP, Telegram, Cloudflare 등의 별도 중계는 사용하지 않는다.
- ChatGPT가 GitHub에 작업 명령을 등록한다.
- GitHub Actions가 명령을 감지하고 Cline CLI를 자동 실행한다.
- Cline이 Unity 프로젝트를 작업하고 자체 검증한다.
- 양방향 ChatGPT ↔ Cline 통신은 필수가 아니다.

## 중복 실행 방지

```text
명령 생성
  ↓
Command ID 부여
  ↓
GitHub 등록
  ↓
처리 여부 확인
  ├─ 처리됨 → 종료
  └─ 미처리 → Cline 실행
                 ↓
              작업/검증
                 ↓
              완료 기록
```

- Command ID로 동일 명령 재실행 방지
- 처리 상태 기록
- GitHub Actions concurrency 적용

## 로드맵
1. Cline 공식 GitHub Actions 연동 구성
2. ChatGPT → GitHub 명령 등록 구현
3. Command ID / 처리 상태 구현
4. Cline 자동 실행 테스트
5. Unity 프로젝트 연결
6. 실제 Unity 작업 및 Cline 자체 검증
7. 전체 자동화 안정화
8. CompanyGameV2 본 개발

## 기록 규칙
- 앞으로 개발 문서는 `Project/Doc/` 안에 날짜 형식으로 추가한다.
- 형식: `YYYYMMDD-내용.md`
- 기존 문서는 덮어쓰지 않는다.
- 새로운 개발 내용은 새로운 날짜 문서로 기록한다.
