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
- 기존 CompanyGameAgent / Bridge / Agent Queue 구조는 폐기한다.
- MCP, Telegram, Cloudflare 등의 별도 중계는 사용하지 않는다.
- ChatGPT가 GitHub에 작업 명령을 등록한다.
- GitHub Actions가 명령을 감지하고 Cline CLI를 자동 실행한다.
- Cline이 Unity 프로젝트를 작업하고 자체 검증한다.
- 양방향 ChatGPT ↔ Cline 통신은 필수가 아니다.

## 로드맵
1. Cline 공식 GitHub Actions 연동 구성
2. ChatGPT → GitHub 명령 등록 구현
3. Cline 자동 실행 테스트
4. Unity 프로젝트 연결
5. 실제 Unity 작업 및 Cline 자체 검증
6. 전체 자동화 안정화
7. CompanyGameV2 본 개발

## 문서 작성 규칙
- `Project/Doc/`는 개발 플로우차트와 로드맵 문서를 모아두는 폴더다.
- 앞으로 모든 문서는 **날짜 + `Flowchart`** 형식으로 만든다.
- 파일명 형식: `YYYYMMDD-Flowchart.md`
- 기존 날짜 문서는 덮어쓰지 않는다.
- 새로운 개발 내용이나 플로우 변경은 새로운 날짜의 `YYYYMMDD-Flowchart.md`로 기록한다.
