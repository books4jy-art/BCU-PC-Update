package io;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

/**
 * BCU KR: text the core's language files don't have yet for things the core already supports. For a proc*.json
 * (ability names and descriptions), entries missing from the file BCU loads are added from resources
 * bcukr/&lt;file&gt;, e.g. "Shortened CD" (CDDEC, added in game version 15.7), with the wording BCU's PackPack bot uses.
 * Entries the loaded file has are never replaced, so a newer core or downloaded file wins.
 * For interface text (page/info/internet/util.properties), {@link #text} gives entries missing from the downloaded
 * language file from bcukr/&lt;name&gt;_&lt;language&gt;.properties, e.g. Korean names of talents the Korean game doesn't have
 * yet; and bcukr/&lt;name&gt;_&lt;language&gt;_override.properties replaces names so they read as in the Korean game.
 */
public class LangExtra {

	private static final Map<String, Properties> TEXT = new HashMap<>();

	/** Interface text for key in resource bcukr/name_code.properties, or null. */
	public static synchronized String text(String name, String code, String key) {
		Properties p = TEXT.get(name + "_" + code);
		if (p == null) {
			p = new Properties();
			InputStream in = ClassLoader.getSystemResourceAsStream("bcukr/" + name + "_" + code + ".properties");
			if (in != null)
				try (InputStreamReader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
					p.load(r);
				} catch (IOException e) {
					e.printStackTrace();
				}
			TEXT.put(name + "_" + code, p);
		}
		return p.getProperty(key);
	}

	public static InputStream addMissing(String file, InputStream in) {
		if (in == null || !file.startsWith("proc") || !file.endsWith(".json"))
			return in;
		InputStream extra = ClassLoader.getSystemResourceAsStream("bcukr/" + file);
		if (extra == null && ClassLoader.getSystemResource("bcukr/" + file.replace(".json", "_override.json")) == null)
			return in;
		byte[] original;
		try {
			original = readAll(in);
		} catch (IOException e) {
			e.printStackTrace();
			return null;
		}
		try {
			JsonObject base = JsonParser.parseReader(new InputStreamReader(new ByteArrayInputStream(original),
					StandardCharsets.UTF_8)).getAsJsonObject();
			if (extra != null) {
				JsonObject add = JsonParser.parseReader(new InputStreamReader(extra, StandardCharsets.UTF_8))
						.getAsJsonObject();
				for (Map.Entry<String, JsonElement> e : add.entrySet())
					if (!base.has(e.getKey()))
						base.add(e.getKey(), e.getValue());
			}
			overrideNames(file, base);
			return new ByteArrayInputStream(base.toString().getBytes(StandardCharsets.UTF_8));
		} catch (Exception e) {
			e.printStackTrace();
			return new ByteArrayInputStream(original);
		} finally {
			try {
				if (extra != null)
					extra.close();
			} catch (IOException ignored) {
			}
		}
	}

	/**
	 * Replaces ability names (abbr_name, full_name; not descriptions) with those in resources
	 * bcukr/&lt;file&gt;_override.json, e.g. the Korean game's own names in proc_kr_override.json.
	 */
	private static void overrideNames(String file, JsonObject base) {
		InputStream in = ClassLoader.getSystemResourceAsStream("bcukr/" + file.replace(".json", "_override.json"));
		if (in == null)
			return;
		try (InputStreamReader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
			JsonObject ov = JsonParser.parseReader(r).getAsJsonObject();
			for (Map.Entry<String, JsonElement> e : ov.entrySet()) {
				if (!e.getValue().isJsonObject() || !base.has(e.getKey()) || !base.get(e.getKey()).isJsonObject())
					continue;
				JsonObject target = base.getAsJsonObject(e.getKey());
				for (String field : new String[] { "abbr_name", "full_name" })
					if (e.getValue().getAsJsonObject().has(field))
						target.add(field, e.getValue().getAsJsonObject().get(field));
			}
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}

	private static byte[] readAll(InputStream in) throws IOException {
		try (InputStream is = in) {
			ByteArrayOutputStream out = new ByteArrayOutputStream();
			byte[] buf = new byte[8192];
			int n;
			while ((n = is.read(buf)) > 0)
				out.write(buf, 0, n);
			return out.toByteArray();
		}
	}
}
