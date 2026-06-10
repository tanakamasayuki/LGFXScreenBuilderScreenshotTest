// Screenshot capture for LGFXScreenBuilder galleries.
//
// Renders every profile x every scene to output/<profile>__<scene>.png using
// the headless SDL backend (lang-ship:host:host:mode=lgfx). Each profile gets
// its own off-screen LGFX device sized to the profile's native resolution, so
// one run captures the whole matrix regardless of the physical board.
//
// 画面定義の全プロファイル x 全シーンを output/<profile>__<scene>.png に
// 書き出す。lang-ship:host の mode=lgfx（ヘッドレス SDL）で動作する。
// プロファイルごとにそのネイティブ解像度の LGFX デバイスを生成するため、
// 物理ボードに依存せず 1 回の実行で全組み合わせをキャプチャできる。
#include <LovyanGFX.hpp>
#include <LGFX_AUTODETECT.hpp>
#include <LGFXScreenBuilder.h>
#include "../Sfm.h"

#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

using namespace Sfm;

// Encode the current framebuffer of `src` as PNG and write it to `path`.
// PNG にエンコードしてファイルへ書き出す。
static bool save_png(LovyanGFX &src, const char *path)
{
    size_t len = 0;
    void *png = src.createPng(&len, 0, 0, src.width(), src.height());
    if (!png || len == 0)
        return false;
    FILE *fp = fopen(path, "wb");
    bool ok = false;
    if (fp)
    {
        ok = (fwrite(png, 1, len, fp) == len);
        fclose(fp);
    }
    free(png);
    return ok;
}

void setup()
{
    Serial.begin(115200);
    Serial.println("TEST start screenshot");

    mkdir("output", 0755);

    for (uint8_t pi = 0; pi < detail::kProfileInfoCount; ++pi)
    {
        const auto &prof = detail::kProfileInfo[pi];

        // Off-screen SDL device at the profile's native resolution.
        // プロファイルのネイティブ解像度でオフスクリーン SDL デバイスを生成。
        LGFX dev(prof.w, prof.h);
        dev.init();

        Screen screen(dev);
        screen.setProfile(static_cast<Profile>(prof.index + 1));
        screen.begin();

        for (uint16_t si = 0; si < detail::kSceneInfoCount; ++si)
        {
            const auto &sc = detail::kSceneInfo[si];
            screen.show(sc.id); // default preview strings = design state

            char path[160];
            snprintf(path, sizeof(path), "output/%s__%s.png", prof.name, sc.name);
            const bool ok = save_png(dev, path);

            Serial.print(ok ? "SHOT ok " : "SHOT fail ");
            Serial.print(prof.name);
            Serial.print(' ');
            Serial.println(sc.name);
        }
    }

    Serial.println("TEST done");
}

void loop()
{
    delay(1000);
}
