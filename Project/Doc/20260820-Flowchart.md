# 2026-08-20 — CompanyGameV2 개발 플로우 / 로드맵

## 최종 확정 플로우

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
Unity 프로젝트
```

## 역할

- **ChatGPT**: 사용자의 개발 명령을 GitHub에 전달한다.
- **GitHub**: 작업 명령과 Unity 프로젝트의 저장소 역할을 한다.
- **GitHub Actions**: GitHub의 프로젝트를 작업 환경으로 가져오고 Cline CLI를 자동 실행한다.
- **Cline CLI**: 준비된 작업 환경의 Unity 프로젝트를 읽고 수정하며 자체 검증한다.
- **Unity**: Cline이 실제로 개발하는 프로젝트다.

## 중요한 구조

Cline이 사용자의 GitHub를 직접 들여다보는 구조가 아니다.

```text
GitHub Repository
      ↓
GitHub Actions가 프로젝트 checkout
      ↓
작업 환경 준비
      ↓
Cline CLI 실행
      ↓
Cline이 해당 작업 환경의 Unity 프로젝트 작업
```

## 핵심 방향

- 기존 CompanyGameAgent / Bridge / Agent Queue 구조는 폐기한다.
- MCP, Telegram, Cloudflare 등의 별도 중계는 사용하지 않는다.
- ChatGPT가 GitHub에 작업 명령을 등록한다.
- GitHub Actions가 명령을 감지하고 Cline CLI를 자동 실행한다.
- Cline이 Unity 프로젝트를 작업하고 자체 검증한다.
- 양방향 ChatGPT ↔ Cline 통신은 필수가 아니다.

## 로드맵

1. Unity 프로젝트와 GitHub Repository 연결
2. Cline 공식 GitHub Actions 연동 구성
3. ChatGPT → GitHub 명령 등록 구현
4. Cline 자동 실행 테스트
5. 실제 Unity 작업 및 Cline 자체 검증
6. 전체 자동화 테스트
7. CompanyGameV2 본 개발

## 문서 작성 규칙

- `Project/Doc/`는 개발 플로우차트와 로드맵 문서를 모아두는 폴더다.
- 앞으로 모든 문서는 **날짜 + `Flowchart`** 형식으로 만든다.
- 파일명 형식: `YYYYMMDD-Flowchart.md`
- 기존 날짜 문서는 덮어쓰지 않는다.
- 새로운 개발 내용이나 플로우 변경은 새로운 날짜의 `YYYYMMDD-Flowchart.md`로 기록한다.
