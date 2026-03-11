<p align="center">
<img src="https://i.imgur.com/x8rtGr4.gif" alt="3D Game Shaders For Beginners" title="3D Game Shaders For Beginners">
</p>

# 3D Game Shaders For Beginners

Interested in adding
textures,
lighting,
shadows,
normal maps,
glowing objects,
ambient occlusion,
reflections,
refractions,
and more to your 3D game?
Great!
Below is a collection of shading techniques that will take your game visuals to new heights.
I've explained each technique in such a way that you can take what you learn here and apply/port it to
whatever stack you use—be it Godot, Unity, Unreal, or something else.
For the glue in between the shaders,
I've chosen the fabulous Panda3D game engine and the OpenGL Shading Language (GLSL).
So if that is your stack, then you'll also get the benefit of learning how to use these
shading techniques with Panda3D and OpenGL specifically.

## Table Of Contents

- [Setup](sections/setup.md)
- [Building The Demo](sections/building-the-demo.md)
- [Running The Demo](sections/running-the-demo.md)
- [Reference Frames](sections/reference-frames.md)
- [GLSL](sections/glsl.md)
- [Render To Texture](sections/render-to-texture.md)
- [Texturing](sections/texturing.md)
- [Lighting](sections/lighting.md)
- [Blinn-Phong](sections/blinn-phong.md)
- [Fresnel Factor](sections/fresnel-factor.md)
- [Rim Lighting](sections/rim-lighting.md)
- [Cel Shading](sections/cel-shading.md)
- [Normal Mapping](sections/normal-mapping.md)
- [Deferred Rendering](sections/deferred-rendering.md)
- [Fog](sections/fog.md)
- [Blur](sections/blur.md)
- [Bloom](sections/bloom.md)
- [SSAO](sections/ssao.md)
- [Motion Blur](sections/motion-blur.md)
- [Chromatic Aberration](sections/chromatic-aberration.md)
- [Screen Space Reflection](sections/screen-space-reflection.md)
- [Screen Space Refraction](sections/screen-space-refraction.md)
- [Foam](sections/foam.md)
- [Flow Mapping](sections/flow-mapping.md)
- [Outlining](sections/outlining.md)
- [Depth Of Field](sections/depth-of-field.md)
- [Posterization](sections/posterization.md)
- [Pixelization](sections/pixelization.md)
- [Sharpen](sections/sharpen.md)
- [Dilation](sections/dilation.md)
- [Film Grain](sections/film-grain.md)
- [Lookup Table (LUT)](sections/lookup-table.md)
- [Gamma Correction](sections/gamma-correction.md)

## License

The included license applies only to the software portion of 3D Game Shaders For Beginners—
specifically the `.cxx`, `.vert`, and `.frag` source code files.
No other portion of 3D Game Shaders For Beginners has been licensed for use.

## Attributions

- [Kiwi Soda Font](https://fontenddev.com/fonts/kiwi-soda/)

## Copyright

(C) 2019 David Lettier
<br>
[lettier.com](https://www.lettier.com)

## Telegram bot: BTCUSDT 5m volumes (Binance + Bybit)

Added helper script `telegram_volume_bot.py` that sends every 5 minutes quote trading volume in **USDT** of the latest **closed** 5m candle for:

- Binance Futures `BTCUSDT`
- Binance Spot `BTCUSDT`
- Bybit Futures `BTCUSDT`
- Bybit Spot `BTCUSDT`

### Run

```bash
python3 -m venv .venv
source .venv/bin/activate
# optional: pip install -r requirements-telegram-bot.txt

export TELEGRAM_BOT_TOKEN="<your_bot_token>"
export TELEGRAM_CHAT_ID="<your_chat_id>"
python3 telegram_volume_bot.py
```

Optional:

```bash
export SEND_ON_START=false
```

If `SEND_ON_START=true` (default), bot sends one report immediately and then continues on each 5-minute boundary.

You can also create a `.env` file in the project root and run without exporting variables each time:

```env
TELEGRAM_BOT_TOKEN=<your_bot_token>
TELEGRAM_CHAT_ID=<your_chat_id>
SEND_ON_START=true
```

Then just run:

```bash
python3 telegram_volume_bot.py
```

## Telegram bot: BTCUSDT futures low-volume alerts (5m)

Added `telegram_futures_alert_bot.py` that checks 5m **futures** quote volume (USDT) for `BTCUSDT` on:

- Binance Futures
- Bybit Futures

It sends a Telegram alert only when at least one exchange has volume **≤ 25,000,000 USDT** on the latest closed 5m candle.

After an alert is sent, the bot enforces a **30-minute cooldown** before the next alert, while still checking the condition every 5 minutes.

### Run

```bash
python3 telegram_futures_alert_bot.py
```

The script reads `.env` with:

```env
TELEGRAM_BOT_TOKEN=<your_bot_token>
TELEGRAM_CHAT_ID=<your_chat_id>
```
