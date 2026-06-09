# Sudoku Cracker

---

> Solve any Sudoku puzzle in seconds.

## Attributions

---

<a href="https://www.flaticon.com/free-icons/unlocked" title="unlocked icons">Unlocked icons created by Freepik - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/sudoku" title="sudoku icons">Sudoku icons created by Freepik - Flaticon</a>

## Setup

---

Install app dependencies:

```bash
uv sync
```

### Development Setup

Install development dependencies:

```bash
uv sync --all-extras
```

Install and run pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

## Build

---

Buildozer packages this Kivy app into an APK using [python-for-android](https://python-for-android.readthedocs.io/). Configuration lives in [`buildozer.spec`](buildozer.spec).

**Further reading:**

- [Buildozer installation](https://buildozer.readthedocs.io/en/latest/installation.html)
- [Buildozer quickstart](https://buildozer.readthedocs.io/en/latest/quickstart.html)
- [Buildozer specifications](https://buildozer.readthedocs.io/en/latest/specifications.html)
- [Kivy Android packaging guide](https://kivy.org/doc/stable/guide/packaging-android.html)

Buildozer runs on **Linux or macOS only** (on Windows, use WSL2 with a Linux distro).

#### 1. Install system dependencies

On Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
  pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake \
  libffi-dev libssl-dev
```

Ensure `adb` is available (for deploy). It ships with Android platform-tools, or install via:

```bash
sudo apt install -y adb
```

#### 2. Prepare your Android device

1. Enable **Developer options** and **USB debugging** on the device.
2. Connect the device via USB.
3. Confirm it is detected:

```bash
adb devices
```

You should see your device listed as `device` (not `unauthorized`). If unauthorized, accept the debugging prompt on the phone and run `adb devices` again.

#### 3. Build the debug APK

From the project root:

```bash
buildozer -v android debug
```

The first build downloads the Android SDK/NDK and compiles native dependencies (including numpy). Expect **30–60+ minutes** on the first run; later builds are much faster. Cached SDK/NDK files are stored under `~/.buildozer/`.

On success, the APK is written to `bin/`.

#### 4. Deploy and run on a connected device

With the device connected:

```bash
buildozer android deploy run
```

Or build, install, and launch in one step:

```bash
buildozer android debug deploy run
```

To stream logs:

```bash
buildozer android debug deploy run logcat
```

#### Common errors and quick fixes

| Error | Fix |
|-------|-----|
| `in order to build Numpy you must set minimum NDK api (minapi) to 24` | Already set in `buildozer.spec` (`android.minapi = 24`, `android.ndk_api = 24`). Do not lower these values. |
| `adb devices` shows `unauthorized` | Unlock the phone and accept the USB debugging authorization dialog. |
| `adb devices` shows no devices | Try another USB cable/port; confirm USB debugging is enabled. |
| Buildozer stuck on SDK license prompt | `android.accept_sdk_license = True` is set in `buildozer.spec`. If prompted manually, type `y` and press Enter. |

#### Scope - What's packaged

`buildozer.spec` bundles only application source and assets:

- `main.py`
- `modules/` (Python files)
- `assets/` (PNG images, including the app icon)

The `tests/` directory is excluded. Runtime requirements are `python3`, `kivy`, and `numpy` (see `requirements` in `buildozer.spec`).

