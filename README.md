# Battle Cats Ultimate
###### A fan-made program featuring data and animations in The Battle Cats by PONOS, along with custom content.
###### Last Written: July 21st, 2024

## This copy: BCU KR

### ⬇️ [Download BCU KR](https://github.com/books4jy-art/BCU-PC-Update/releases/latest)

Open the latest release, download **BCU-KR-….zip**, unzip it into its own folder, install
[Java](https://www.java.com/en/download/manual.jsp) (8 or newer, 64-bit) and start **BCU-KR.jar**. The first start
downloads BCU's game data (several hundred MB). It keeps its data and settings in its own folder, apart from any
official BCU. See `README.txt` in the zip (English and Korean).

Not made by me: Battle Cats Ultimate is by the BCU team ([battlecatsultimate](https://github.com/battlecatsultimate));
Battle Cats is © PONOS.

This is [BCU-java-PC](https://github.com/battlecatsultimate/BCU-java-PC) (`slow_kotlin`, 0.5.8.8) with its full
history, set up for the game's country versions (Korea by default). BCU's own code (the core, `src/main/java/common`,
a submodule of [BCU_java_util_common](https://github.com/battlecatsultimate/BCU_java_util_common)) is not edited.

What's different from the official BCU:

- **Core 0.7.20.0** (BCU_java_util_common `data_focus`, the core that reads BCU's newest asset packs, game version
  15.5).
- **Country versions** (Configuration > Game version; Korea by default; applies when BCU next starts): the game's
  versions of files that differ from BCU's (Japanese 15.5) ones, from version 15.6.0 of each country in
  [fieryhenry/BCData](https://git.battlecatsmodding.org/fieryhenry/BCData/src/commit/2a49665d0135283dc5c86e8d5825bb120b2849d7/game_data),
  shipped inside the jar (`src/main/resources/country/<kr|jp|en|tw>`) and put in place of BCU's files after the
  asset packs are read (`src/main/java/io/CountryData.java`, called from `MainBCU`):
  - Korea 15.6: 95 stages, talents, orb slots, cat prices, 1 cat's stats, plus 78 Korean enemy bases and
    backgrounds from the Korean server packs;
  - Japan 15.6 (newer than BCU's 15.5): 14 stages, talents, orb slots, cat prices, 2 cats' stats;
  - English 15.6 and Taiwan 15.6: 68 stages each, talents, orb slots, cat prices, 1 cat's stats;
  - or BCU's own data unchanged. The choice is kept in `user/game_version.txt`.

  `tools/country_data.py` makes these and only takes what BCU can use safely: no stage that needs enemies,
  backgrounds or enemy bases BCU doesn't have, no cat form or spirit BCU has no pictures for, no placeholder data
  for unreleased or removed cats, no table missing rows for cats or enemies BCU has, no talent types the core
  doesn't know, no combos with cats BCU doesn't have.
- **Never offers the official jars as updates** (`io/BCJSON.java`), so it isn't replaced by the official BCU.
- **One download**: `BCU-KR.jar` with its libraries in `lib/`, built from the command line.

### Updating the country data

```sh
python3 tools/country_data.py kr --keep-images   # --keep-images keeps the Korean pictures (not in DataLocal)
python3 tools/country_data.py jp                 # also en, tw; --version for another game version
```

### Building

Needs JDK 17 or newer (Gradle downloads it if missing); the jar runs on Java 8.

```sh
git submodule update --init
./gradlew bcuKrZip --no-configuration-cache   # build/dist/BCU-KR-<version>.zip
```

### Publishing a release

The "Release" workflow (`.github/workflows/release.yml`) builds the zip and publishes it as a GitHub Release. Start
it under Actions > "Release" > Run workflow (or push a tag such as `v0.5.8.8-kr2`). For a new version, raise
`bcuKrVersion` in `build.gradle.kts` first.

### Updating from BCU

```sh
git remote add upstream https://github.com/battlecatsultimate/BCU-java-PC   # once
git fetch upstream && git merge upstream/slow_kotlin
cd src/main/java/common && git fetch origin && git checkout <core commit> && cd -   # newer core, if wanted
```

---

## Installing BCU Version 5 for Windows, macOS, or Linux

1. Download and install [the JRE](https://www.java.com/en/download/manual.jsp) that corresponds to your operating system.
    - For macOS users, you might want to download [JDK 8](https://drive.google.com/file/d/1tX-LQygjt3w0x3uQnyHBC2O-uePUQrPn/view?usp=sharing) as well in the case that BCU fails to work properly, especially if JOGL is enabled.
2. Download [BCU-Initializer.jar](https://github.com/battlecatsultimate/bcu-assets/raw/master/jar/BCU-Initializer.jar)
3. Move the jar to a new, empty folder, then run the jar.

## Frequently Asked Questions
### How do I create custom content? / How do I animate?
Refer to the links below with the label "BCU Tutorial" under the **Links & Resources** section.

### Common Issues/Errors
If none of these apply to your situation, you can report it through GitHub Issues or the BCU English Discord server, linked below. Make sure to include the most recent error log, which should be the newest .log file in the `log` folder.
- If you're able to open BCU, you can also find the latest log file through the `Error Logs` button in the main menu.

#### All Platforms
- *Another BCU is running or last BCU didn't close properly*
    - If the last BCU crashed, this will be the default message.
    - It's advised to avoid running two BCU instances at the same time, as well as allowing BCU to close properly.
    - If there was a real problem that seemed to have caused the crash, follow the above instructions to report the problem.
- *Not enough memory*
    - Open up BCU again. In the main menu, If the number on the top left says `# / 247 MB` and your computer is 64-bit, you installed the wrong Java. Install 64-bit Java instead.
    - If the above fails, you may need to use run.bat, which is available in the BCU Discord server, linked below.

#### Windows Issues and Warnings

Don't install `Windows Online` installer if your OS type is 64-bit. You will have to download `Windows Offline (64-bit)` one.
It's fine to install `Windows Online` or `Windows Offline` if your OS type is 32-bit. If you install incorrect JRE, BCU will have memory space issue.

**Do not run BCU with `Open with Java` option!** This will connect BCU with `system32` folder, and BCU will try to create subfolders in there.

Below is issue related with Windows that commonly happens.

- Windows open jar file with incorrect program such as WinRAR, etc
    - First of all, do not extract jar file. Jar files are executable file like exe, not something supposed to be extracted.
    - Follow steps below to change program connection.
    1. Click BCU jar file once
    2. Put mouse on jar file, and right click it
    3. Click `Properties`
    4. Click `Change...` next to `Open With`
    5. Program list will appear, select Java
    6. Close properties windows by clicking `Apply` and `OK`

#### macOS Issues
Some issues below can be fixed by running the jar via Terminal. If it suggests doing this, follow these instructions.
1. Open Launchpad and search up "Terminal", then open up the program.
2. Change the Terminal's current working directory to your BCU folder.
    1. Type `cd` into the Terminal, with a space after.
    2. Go to your finder and find the BCU folder.
    3. Drag and drop the BCU folder icon onto the Terminal window.
    4. Press the Enter key.
3. Run the jar through your terminal.
    1. Type `java -jar` into the Terminal, with a space after.
    2. In your BCU folder, locate the jar you will run.
    3. Drag and drop the jar onto the Terminal window.
    4. Press the Enter key.
  
- *The files downloaded are not in the BCU folder (For example, the `BCU_lib` folder was not downloaded automatically into your BCU folder)*
    - Follow the instructions above to use Terminal.
- *WARNING: NSWindow drag regions should only be invalidated on the Main Thread! This will throw an exception in the future.*
    - This usually happens only if JOGL is enabled. In order to keep JOGL on, make sure your JDK version is 8, then follow the instructions above to use Terminal.
    - NOTE: As of July 2024, this should no longer be occurring. If this is something you are experiencing, please report it through either GitHub Issues or in the BCU English Discord server!
  
#### Linux Issues
Most common issue on linux is making sure the correct java version is used when launching BCU. Depending on your distro, you can swap your default java very easy. The current java version required for BCU is java 8.
- For Arch Linux distros, use `archlinux-java status` to check your current default java. If it's incorrect, use `archlinux-java set java-8-openjdk` to swap to java 8 as default. You may need to run this command with sudo.
- For Debian/Ubuntu Linux distros, use `sudo update-alternatives --config java`. It will bring up all installed versions of java with the current active one marked and provides a dialog to help switch.
- For Fedora Linux distros, use `sudo alternatives --config java`. It will bring up all installed versions of java with the current active one marked and provide a dialog to help switch.

If you have trouble launching BCU via Linux's GUI, open terminal and navagate to the folder where the bcu jar file is and use `java -jar nameofbcu.jar` to launch it.

## Links & Resources

- [BCU Tutorial - Animating](https://docs.google.com/document/d/1X2UZGEJzkSTXjgvozQRgKoHSjCpsHt4Eh94sllPu8JQ/edit?usp=sharing)
- [BCU Tutorial - Custom Content](https://docs.google.com/document/d/1k682-1xNnHH3Z4sq6MhB4s7TgtyPqMKZUFwydsXcOiw/edit)

### The BCU Discords
- [BCU English Server](https://discord.gg/zvqamBW)
- [至BCU中文伺服器](https://discord.gg/uyyarVR)
- [BCU 한국 서버 링크](https://discord.gg/fZZnZsw)
- [日本語BCU招待リンク](https://discord.gg/kBB9Qyv3E9)
