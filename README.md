# 인체 해부학 3D 아틀라스

실제 인체 데이터(BodyParts3D)로 만든 전신 3D 해부학 학습 사이트입니다.

사이트: https://parksang0521.github.io/anatomy-3d/

- 뼈(치아·연골 포함) 276개, 뇌·눈 117개, 장기, 근육 414개, 동맥 426개, 정맥 225개 — 약 1,550개 구조물을 각각 선택 가능
- 척수·척수신경 31쌍·팔/허리/엉치신경얼기와 주요 말초신경·교감신경줄기·뇌신경 (근사 경로 모델)
- 신경·근육·동맥·정맥은 켤 때 불러옴(처음 로딩 약 6MB, 전체 약 12MB)
- 단면 보기(가로·시상·관상면), 계통별 투명도, 구조물별 공유 링크(#주소)
- 남성/여성 모델 전환, 생식계(남: 고환·부고환·정관·정낭·전립샘·음경 / 여: 자궁·난소·자궁관·유방)
- 사이드바 접기, 퀴즈 패널을 오른쪽에 고정해 모델이 가려지지 않게 함
- 주요 근육은 기시·정지·신경·작용, 주요 혈관은 주행·임상 포인트 설명
- 구조물 클릭 → 새 용어 / 구 용어 / 영문 명칭, 설명, 핵심 포인트, 임상 연관
- 계통별 켜기/끄기, 검색, 뼈 X-ray 모드, 피부 윤곽, 시점 전환, 한 구조물만 보기
- 퀴즈: 이름 맞히기 / 위치 찾기

## 데이터 출처 및 라이선스

- 3D 모델: **BodyParts3D**, © The Database Center for Life Science (DBCLS), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  - https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
  - 대부분의 구조물은 BodyParts3D 4.0을 브라우저용으로 경량화한 [ashemag/human-atlas](https://github.com/ashemag/human-atlas)(MIT)의 데이터를 사용
  - 허파 5엽과 간은 BodyParts3D 3.0 데이터([Kevin-Mattheus-Moerman/BodyParts3D](https://github.com/Kevin-Mattheus-Moerman/BodyParts3D) 사본)를 4.0 좌표에 맞춰 정렬·경량화해 추가
  - 변경 사항: 구조물 선별, 메쉬 단순화, 좌표 양자화, 계통별 재구성, 한국어 명칭 부여
- 척수·말초신경·대부분의 뇌신경: 원본 데이터에 없어, 주변 뼈·혈관·근육 메쉬에서 계산한 기준점으로 경로를 만든 근사 모델 (`build/nerves.py`)
- 여성 모델: [HuBMAP Human Reference Atlas 3D Reference Object Library](https://humanatlas.io/3d-reference-library) (Visible Human Female 기반), CC BY 4.0 — 장기·골반·무릎·혈관·척수·유방·여성 생식기관. 머리뼈·갈비뼈·팔뼈·근육·말초신경은 포함되지 않음
- 설명 문구: 직접 작성

> 성인 남성 1인의 기준 모델로 개인차를 반영하지 않습니다. 교육용이며 진단·수술용이 아닙니다.
