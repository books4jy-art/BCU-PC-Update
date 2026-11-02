package io;

import common.CommonStatic;
import common.system.files.FDByte;
import common.system.files.VFile;
import common.system.files.VFileRoot;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

/**
 * BCU KR: which country's version of the game to play. BCU's own data is the Japanese game's (15.5); the other
 * choices use that country's versions of files that differ from BCU's, shipped inside the jar (resources
 * country/<code>, listed in country/<code>/files.json as path -> size, made by tools/country_data.py from
 * fieryhenry's BCData 15.6.0): stage files, cat stats, cat prices, talents and orb slots where they differ and BCU
 * can use them, and for Korea also its enemy bases and backgrounds. They replace BCU's file of the same path in the
 * core's file tree, after the asset packs are read and before the game data is loaded (MainBCU's initProfile).
 * The choice is kept in user/game_version.txt in the BCU folder; it applies when BCU starts.
 */
public class CountryData {

	/** Codes and names, in the order of the settings list; "" = BCU's own data. */
	public static final String[] CODES = { "kr", "jp", "en", "tw", "" };
	public static final String[] NAMES = { "Korea 15.6", "Japan 15.6", "English 15.6", "Taiwan 15.6", "BCU (Japan 15.5)" };
	public static final String[] NAMES_KR = { "한국판 15.6", "일본판 15.6", "영어판 15.6", "대만판 15.6", "BCU 기본 (일본판 15.5)" };

	/** This copy's default: the Korean version. */
	public static final String DEFAULT = "kr";

	private static File file() {
		return new File(CommonStatic.ctx.getBCUFolder(), "./user/game_version.txt");
	}

	public static String chosen() {
		try {
			File f = file();
			if (f.exists()) {
				String code = new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8).trim();
				for (String c : CODES)
					if (c.equals(code))
						return c;
			}
		} catch (IOException ignored) {
		}
		return DEFAULT;
	}

	public static void choose(String code) {
		try {
			File f = file();
			if (f.getParentFile() != null)
				f.getParentFile().mkdirs();
			Files.write(f.toPath(), code.getBytes(StandardCharsets.UTF_8));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/** Puts the chosen country's files into the file tree; returns how many. */
	public static int apply() {
		String code = chosen();
		if (code.isEmpty())
			return 0;
		String dir = "/country/" + code + "/";
		byte[] list = read(dir + "files.json");
		if (list == null)
			return 0;
		JsonObject files = JsonParser.parseString(new String(list, StandardCharsets.UTF_8)).getAsJsonObject();
		VFileRoot root = VFile.getBCFileTree();
		int n = 0;
		for (String path : files.keySet()) {
			// "./org/stage/..." is shipped as country/<code>/stage/...
			byte[] bytes = read(dir + path.substring("./org/".length()));
			if (bytes == null)
				continue;
			root.build(path, new FDByte(bytes));
			n++;
		}
		return n;
	}

	private static byte[] read(String resource) {
		try (InputStream is = CountryData.class.getResourceAsStream(resource)) {
			if (is == null)
				return null;
			ByteArrayOutputStream out = new ByteArrayOutputStream();
			byte[] buf = new byte[16384];
			int r;
			while ((r = is.read(buf)) > 0)
				out.write(buf, 0, r);
			return out.toByteArray();
		} catch (IOException e) {
			return null;
		}
	}
}
