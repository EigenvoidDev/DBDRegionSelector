# DBDRegionSelector

[Dead by Daylight](https://deadbydaylight.com/) is an online asymmetric multiplayer survival horror video game developed and published by Canadian studio [Behaviour Interactive](https://www.bhvr.com/).

**DBDRegionSelector** is a desktop GUI tool that allows you to control which AWS regions Dead by Daylight can connect to. It provides real-time latency and packet loss metrics for all supported regions and offers a simple interface for blocking or unblocking access to specific ones through `hosts` file rules.

## Installation and Usage

### Option 1: Run from Source

If you are running the application from source (e.g., cloned from GitHub), make sure you have [Python 3.9 or higher](https://www.python.org/downloads/) installed, and install [PyQt6](https://pypi.org/project/PyQt6/) using pip:
```
pip install PyQt6
```
Next, open a terminal, navigate to the application's root directory, and run:
```
python main.py
```

**Note:** Region selection features require administrator (or root) access to modify the system's `hosts` file.
- On **Windows**, open the terminal as administrator before running the script.
- On **macOS/Linux**, run the script with `sudo`:
```
sudo python3 main.py
```

### Option 2: Prebuilt Executable

If you are on **Windows**, download the prebuilt executable from the [Releases page](https://github.com/EigenvoidDev/DBDRegionSelector/releases). Once downloaded, simply double-click the file to launch the application.

#### Understanding the UAC Prompt and SmartScreen Warning

This application requires administrator permissions to modify the system's `hosts` file, which is necessary for enabling or blocking Dead by Daylight AWS regions.
- On **Windows Vista and newer**, you will see a UAC (User Account Control) prompt when launching the application.
- On **Windows 8 and newer**, you may also see a SmartScreen warning due to the application being unsigned.

This application is not digitally signed because code-signing certificates require a paid license. As a result, Windows may warn you that the application is from an unknown publisher.

### Antivirus Warnings

Because this application is unsigned and requests administrator permissions, some antivirus software may flag it as suspicious or prevent it from being downloaded.

These detections are **false positives**. You can verify the safety of the application by reviewing the source code directly in this repository or building the executable yourself.

If your antivirus software blocks the application, consider adding it to your allowlist or exclusions.

## Important Note on US East (N. Virginia) Region

You may notice that even after blocking US East (N. Virginia), the game still routes connections through that region. This is because both Easy Anti-Cheat (EAC) and RTM services are hosted there. As a result, N. Virginia cannot be explicitly blocked without disrupting core game functionality.

To minimize the chances of being connected to N. Virginia game servers, you can try combining multiple methods, such as:
- Blocking nearby regions that are more likely to be selected by the matchmaking system.
- Retrying the matchmaking process until you are placed in a different region.

## License

DBDRegionSelector is licensed under the [GNU General Public License v3.0 (GPLv3)](https://github.com/EigenvoidDev/DBDRegionSelector/blob/main/LICENSE).