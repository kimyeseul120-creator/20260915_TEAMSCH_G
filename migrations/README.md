# migrations

현재는 `db.create_all()`로 스키마를 생성합니다 (앱 최초 기동 시 자동 실행).
스키마 변경 이력 관리가 필요해지면 Flask-Migrate(Alembic)를 도입해 이 폴더에
리비전 파일을 두는 구조로 확장할 수 있도록 자리만 비워둡니다.
