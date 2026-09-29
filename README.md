# 제스처 카메라: Stage 4 OBS 효과 MVP

## 빠른 사용 방법

아래 순서대로 설정하고 실행하세요.

1. Unity Capture를 설치하고, `requirements.txt`의 Python 패키지를 설치합니다.
2. OBS를 먼저 실행한 뒤 **도구 → WebSocket 서버 설정**에서 서버를 활성화합니다.
   기본 포트는 `4455`이며, 인증 비밀번호를 사용한다면 `main.py`의
   `OBS_HOST`, `OBS_PORT`, `OBS_PASSWORD`에도 같은 값을 입력합니다.
   어차피 로컬에서 혼자 쓰는 거면 인증 비밀번호 걍 끄세요.
3. OBS에 `GestureCamera` 씬을 만들고, **Unity Video Capture**를 **비디오 캡처 장치**로 추가합니다.
4. 같은 장면에 `effect_thumbs_up`, `effect_victory` 미디어 소스를 추가하고 각 `.webm`
   효과 파일을 연결합니다. 효과 소스는 시작 시 프로그램이 자동으로 숨깁니다.
   main.py에서 추가하거나 빼시면 됩니다. assets에는 샘플 thumbs_up.webm이 있습니다.
5. PowerShell에서 다음 명령으로 프로그램을 실행합니다.

```powershell
.\.venv\Scripts\Activate.ps1
py main.py
```

6. 콘솔에 OBS 씬과 효과 소스 검증이 완료되었다는 메시지가 보이면, 웹캠 앞에서
   엄지척 또는 V 사인을 합니다. OBS에서 해당 효과가 약 2초간 표시됩니다.
7. 종료하려면 Python 미리보기 창에 포커스를 둔 뒤 `q`를 누릅니다.

OBS 실행 및 설정이 Python 프로그램보다 먼저 완료되어야 합니다. 또한 실제 웹캠은
OBS가 아니라 이 프로그램이 사용하므로, OBS에는 반드시 **Unity Video Capture**를
선택해야 합니다.

이 프로젝트는 현재 다음 네 단계만 구현합니다.

```text
실제 웹캠 -> Python/OpenCV -> MediaPipe
                    -> Unity Video Capture -> OBS 배경 영상
제스처 -> OBS WebSocket -> 효과 씬 항목 표시 여부
```

실제 웹캠은 `CameraCapture`만 엽니다. 원본 BGR 프레임은 MediaPipe와 Unity
Capture 양쪽으로 전달됩니다. Python 미리보기는 랜드마크와 제스처 오버레이가
표시되는 별도 복사본이며, 효과 렌더링은 OBS가 직접 수행합니다.

## 파일

- `main.py`: 고정된 카메라 설정, 단일 프레임 루프, 제스처 에지 감지 및
  OBS/효과 매핑 설정을 한곳에서 관리합니다.
- `camera/`: 실제 웹캠 캡처와 Unity Capture `pyvirtualcam` 출력을 담당합니다.
- `recognition/`: MediaPipe 랜드마크 및 제스처 분류를 담당합니다.
- `obs/obs_controller.py`: OBS WebSocket v5 연결, 씬/소스 검증 및 씬 항목
  표시 여부 호출을 담당합니다.
- `obs/effect_manager.py`: 블로킹 없이 한 번에 하나의 활성 효과만 유지하도록 관리합니다.

## Python 설정

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```

`requirements.txt`에는 `obsws-python`이 포함되어 있습니다. Unity Capture는
Python 의존성이 아니라 별도로 설치해야 하는 Windows DirectShow 드라이버입니다.

## OBS WebSocket 설정

OBS Studio 28 이상에는 obs-websocket이 기본 포함되어 있습니다. Python 프로그램을
실행하기 전에 다음과 같이 설정하세요.

1. OBS를 실행합니다.
2. **도구 → WebSocket 서버 설정**을 선택합니다.
3. WebSocket 서버를 활성화합니다.
4. 서버 포트(기본값: `4455`)를 확인합니다.
5. 인증을 사용하는 경우 비밀번호를 복사하거나 설정합니다.
6. `main.py`에 동일한 값을 입력합니다.

```python
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = ""
```

## 필요한 OBS 씬

다음 씬과 소스를 정확히 이 이름으로 만드세요.

```text
GestureCamera
├─ Unity Video Capture
├─ effect_thumbs_up
├─ effect_thumbs_up_1 ... effect_thumbs_up_7
└─ effect_victory
```

`Unity Video Capture`는 계속 표시된 상태여야 합니다. Python은 시작 시 두 효과
소스가 모두 있는지 검증하고, 처리를 시작하기 전에 숨깁니다. 씬 또는 소스 이름이
없으면 명확한 오류와 함께 시작이 중단됩니다.

### 효과 소스 만들기

투명한 `.webm` 효과 파일마다 다음을 수행하세요.

1. **소스**에서 **+ → 미디어 소스**를 선택합니다.
2. 엄지척 소스의 이름은 `effect_thumbs_up`, `effect_thumbs_up_1`부터
   `effect_thumbs_up_7`까지로 지정하고, V 소스의 이름은 `effect_victory`로 지정합니다.
3. **로컬 파일**을 활성화하고 `.webm` 파일을 선택합니다.
4. **소스가 활성화되면 재생 다시 시작**을 활성화한 상태로 둡니다.
5. 일회성 효과를 위해 **반복**은 비활성화합니다.
6. Python이 소스를 숨기기 전에 재생이 끝나더라도 OBS에 마지막 프레임이 남지 않도록
   **재생이 끝나면 아무것도 표시 안 함**을 활성화합니다.

OBS의 [미디어 소스 안내](https://obsproject.com/kb/media-sources)에서 이 미디어
소스 옵션 이름과 동작을 확인할 수 있습니다.

## 제스처-효과 동작

전체 매핑은 `main.py` 상단 부근에 한 번만 정의되어 있습니다.

```python
GESTURE_EFFECT_MAP = {
    "THUMBS_UP": ["effect_thumbs_up", "effect_thumbs_up_1", "...", "effect_thumbs_up_7"],
    "VICTORY": ["effect_victory"],
}
EFFECT_DURATION_SECONDS = 2.0
```

제스처가 없는 상태에서 감지된 상태로 전환될 때만 OBS가 실행됩니다. 같은 제스처를
계속 유지해도 ON 명령을 다시 보내지 않습니다. 손을 내리면 에지 감지기가 초기화되어
나중에 같은 제스처를 다시 실행할 수 있습니다. 한 번에 활성화되는 효과는 최대 하나이며,
새 제스처는 자신의 소스를 켜기 전에 이전 효과를 끕니다. 메인 루프는 매 프레임 만료를
확인하므로 `sleep`, 스레드 또는 비동기 코드가 카메라 처리를 멈추지 않습니다.

## Unity Capture 및 OBS 테스트

1. Unity Capture를 설치/등록한 뒤 OBS를 실행하고 WebSocket을 설정합니다.
2. `py main.py`를 실행하고, 콘솔에서 `GestureCamera`, 엄지척 소스 8개, V 소스가
   검증되는지 확인합니다.
3. OBS에서 **Unity Video Capture**를 `1280x720`의 **비디오 캡처 장치**로 추가하거나 선택합니다.
4. 엄지척을 합니다. `effect_thumbs_up`과 `effect_thumbs_up_*` 소스 7개가 약 2초 동안
   표시되어야 합니다. V 사인으로 `effect_victory`도 반복해 확인합니다.
5. 두 제스처 중 하나를 유지해 봅니다. 반복 실행되지 않아야 합니다. 손을 내렸다가
   다시 제스처를 하면 한 번 더 실행됩니다.
6. `q`를 눌러 종료합니다. 활성 효과가 숨겨진 다음 OBS, Unity Capture, MediaPipe, 웹캠,
   OpenCV 리소스가 닫힙니다.

OBS 가상 카메라, OBS WebSocket 씬 전환, Discord/Zoom, 코드로 생성하는 효과,
제스처 쿨다운/상태 머신, 여러 효과의 동시 실행은 구현되어 있지 않습니다.
