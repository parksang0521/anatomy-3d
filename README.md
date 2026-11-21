# 인체 해부학 3D 아틀라스

실제 인체 데이터(BodyParts3D)로 만든 전신 3D 해부학 학습 사이트입니다.

사이트: https://parksang0521.github.io/anatomy-3d/

- 뼈(치아·연골 포함) 276개, 뇌·눈 117개, 심장·허파·소화·비뇨·내분비 구조물 등 약 480개를 각각 선택 가능
- 구조물 클릭 → 새 용어 / 구 용어 / 영문 명칭, 설명, 핵심 포인트, 임상 연관
- 계통별 켜기/끄기, 검색, 뼈 X-ray 모드, 피부 윤곽, 시점 전환, 한 구조물만 보기
- 퀴즈: 이름 맞히기 / 위치 찾기

## 데이터 출처 및 라이선스

- 3D 모델: **BodyParts3D**, © The Database Center for Life Science (DBCLS), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  - https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
  - 대부분의 구조물은 BodyParts3D 4.0을 브라우저용으로 경량화한 [ashemag/human-atlas](https://github.com/ashemag/human-atlas)(MIT)의 데이터를 사용
  - 허파 5엽과 간은 BodyParts3D 3.0 데이터([Kevin-Mattheus-Moerman/BodyParts3D](https://github.com/Kevin-Mattheus-Moerman/BodyParts3D) 사본)를 4.0 좌표에 맞춰 정렬·경량화해 추가
  - 변경 사항: 구조물 선별, 메쉬 단순화, 좌표 양자화, 계통별 재구성, 한국어 명칭 부여
- 설명 문구: 직접 작성

> 성인 남성 1인의 기준 모델로 개인차를 반영하지 않습니다. 교육용이며 진단·수술용이 아닙니다.
