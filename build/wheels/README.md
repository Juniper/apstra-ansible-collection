# build/wheels/

This directory holds the **Apstra SDK wheel file** required to build the Execution Environment image.

> **The wheel is NOT included in this repository.** You must download it from the Juniper Support portal before running `make pipenv` or `make image`.

## Download the Apstra SDK

1. Go to: **https://support.juniper.net/support/downloads/?p=apstra**
2. Under **"Application Tools"** select **"Apstra Automation Python3 SDK"**.
3. Download the `.tar.gz` archive (e.g. `apstra-automation-python3-sdk-6.1.0.tar.gz`).
4. Extract and place the wheel here:

   ```bash
   tar -xzf apstra-automation-python3-sdk-6.1.0.tar.gz
   cp path/to/aos_sdk-6.1.0-py3-none-any.whl build/wheels/
   ```

5. Then run:

   ```bash
   make pipenv
   make image
   ```

> **Important:** Run `make pipenv` only **after** placing the wheel here.
> If the wheel is absent, `make pipenv` falls back to downloading `aos_sdk-0.1.0`
> (Apstra 5.1 SDK), which is **not compatible** with Apstra 6.0 / 6.1.

## Compatibility

| Wheel file                         | Apstra Server |
|------------------------------------|---------------|
| `aos_sdk-6.1.0-py3-none-any.whl`  | 6.0 / 6.1     |
| `aos_sdk-0.1.0-py3-none-any.whl`  | 5.1.x         |

Wheel files (`*.whl`) are gitignored — they will never be committed to this repository.
