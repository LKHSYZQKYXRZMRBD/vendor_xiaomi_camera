#!/bin/bash
#
# SPDX-FileCopyrightText: 2016 The CyanogenMod Project
# SPDX-FileCopyrightText: 2017-2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

set -e

MY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${MY_DIR}/../../../tools/extract-utils${PYTHONPATH:+:${PYTHONPATH}}"

exec python3 "${MY_DIR}/extract-files.py" "$@"
