# CompanyGameV2 개발 플로우 / 로드맵 기준 문서

이 파일 하나를 앞으로의 **개발 플로우 차트 및 로드맵을 모아두는 기준 문서**로 사용한다.

---

## 20260820 — 초기 자동화 구조 확정

### 플로우 차트
```text
[사용자]
    ↓
[ChatGPT]
    ↓ 작업 명령 등록
[GitHub]
    ↓ 자동 감지
[GitHub Actions]
    ↓ Cline CLI 자동 실행
[Cline]
    ↓ 코드 작성 / 수정 / 실행 / 자체 검증
[Unity]
    ↓
[완성된 작업]
```

### 확정 방향
- 기존 `CompanyGameAgent` / Bridge / Agent Queue 구조는 폐기한다.
- MCP, Telegram, Cloudflare 등의 별도 중계 구조는 사용하지 않는다.
- ChatGPT가 GitHub에 작업 명령을 등록한다.
- GitHub Actions가 명령을 받아 Cline CLI를 자동 실행한다.
- Cline이 Unity 프로젝트를 작업하고 자체 검증한다.
- ChatGPT와 Cline의 양방향 통신은 필수가 아니다.

### 안전장치
```text
명령 생성
  ↓
고유 Command ID 부여
  ↓
GitHub 등록
  ↓
처리 여부 확인
  ├─ 이미 처리됨 → 종료
  └─ 미처리 → Cline 실행
                 ↓
              처리 완료 기록
```

- 동일 명령의 반복 실행을 방지한다.
- GitHub Actions concurrency로 중복 실행을 제한한다.
- 처리 완료 상태를 기록한다.

### 로드맵
1. GitHub Actions + Cline 공식 GitHub 연동 구성
2. ChatGPT → GitHub 명령 등록 방식 구현
3. Command ID / 처리 상태 구현
4. Cline 자동 실행 테스트
5. Unity 프로젝트 연결
6. 실제 Unity 작업 및 Cline 자체 검증 테스트
7. 전체 자동화 안정화
8. CompanyGameV2 본 개발

---

## 기록 규칙
- 앞으로 개발 플로우/로드맵은 **이 `Doc.md` 파일에 날짜별 섹션으로 계속 추가**한다.
- 날짜 형식은 `YYYYMMDD`를 사용한다.
- 기존 날짜의 기록은 덮어쓰지 않는다.
- 새로운 개발 내용은 항상 새 날짜 섹션으로 추가한다.
- `Project` 폴더에 날짜별 문서를 따로 만들지 않는다. **모든 기록은 이 `Doc.md` 하나에 누적한다.**
