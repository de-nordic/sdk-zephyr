"""
Utility script to migrate Zephyr-based projects to new MCUmgr Kconfig options

Usage::

    python $ZEPHYR_BASE/scripts/utils/migrate_mcumgr_kconfigs.py -r root_path

The utility will process c, cpp, h, hpp, rst, conf, CMakeLists.txt,
yml, yaml and Kconfig files.


Copyright (c) 2022 Nordic Semiconductor ASA
SPDX-License-Identifier: Apache-2.0
"""

import argparse
from pathlib import Path
import re
import sys


ZEPHYR_BASE = Path(__file__).parents[2]

FILE_PATTERNS = (
    r".+\.c", r".+\.cpp", r".+\.hpp", r".+\.h", r".+\.rst", r".+\.conf",
    r".+\.yml", r".+\.yaml", r"CMakeLists.txt", r"Kconfig(\..+)?"
)

REPLACEMENTS = {
    "MCUMGR_SMP_WORKQUEUE_STACK_SIZE" : "MCUMGR_TRANSPORT_WORKQUEUE_STACK_SIZE",
    "MCUMGR_SMP_WORKQUEUE_THREAD_PRIO" : "MCUMGR_TRANSPORT_WORKQUEUE_THREAD_PRIO",
    "MGMT_MAX_MAIN_MAP_ENTRIES" : "MCUMGR_SMP_CBOR_MAX_MAIN_MAP_ENTRIES",
    "MGMT_MIN_DECODING_LEVELS" : "MCUMGR_SMP_CBOR_MIN_DECODING_LEVELS",
    "MGMT_MIN_DECODING_LEVEL_1" : "MCUMGR_SMP_CBOR_MIN_DECODING_LEVEL_1",
    "MGMT_MIN_DECODING_LEVEL_2" : "MCUMGR_SMP_CBOR_MIN_DECODING_LEVEL_2",
    "MGMT_MIN_DECODING_LEVEL_3" : "MCUMGR_SMP_CBOR_MIN_DECODING_LEVEL_3",
    "MGMT_MIN_DECODING_LEVEL_4" : "MCUMGR_SMP_CBOR_MIN_DECODING_LEVEL_4",
    "MGMT_MIN_DECODING_LEVEL_5" : "MCUMGR_SMP_CBOR_MIN_DECODING_LEVEL_5",
    "MGMT_MAX_DECODING_LEVELS" : "MCUMGR_SMP_CBOR_MAX_DECODING_LEVELS",
    "MCUMGR_CMD_FS_MGMT" : "MCUMGR_GRP_FS",
    "FS_MGMT_MAX_FILE_SIZE_64KB" : "MCUMGR_GRP_FS_MAX_FILE_SIZE_64KB",
    "FS_MGMT_MAX_FILE_SIZE_4GB" : "MCUMGR_GRP_FS_MAX_FILE_SIZE_4GB",
    "FS_MGMT_MAX_OFFSET_LEN" : "MCUMGR_GRP_FS_MAX_OFFSET_LEN",
    "FS_MGMT_DL_CHUNK_SIZE_LIMIT" : "MCUMGR_GRP_FS_DL_CHUNK_SIZE_LIMIT",
    "FS_MGMT_DL_CHUNK_SIZE" : "MCUMGR_GRP_FS_DL_CHUNK_SIZE",
    "FS_MGMT_FILE_STATUS" : "MCUMGR_GRP_FS_FILE_STATUS",
    "FS_MGMT_CHECKSUM_HASH" : "MCUMGR_GRP_FS_CHECKSUM_HASH",
    "FS_MGMT_CHECKSUM_HASH_CHUNK_SIZE" : "MCUMGR_GRP_FS_CHECKSUM_HASH_CHUNK_SIZE",
    "FS_MGMT_CHECKSUM_IEEE_CRC32" : "MCUMGR_GRP_FS_CHECKSUM_IEEE_CRC32",
    "FS_MGMT_HASH_SHA256" : "MCUMGR_GRP_FS_HASH_SHA256",
    "FS_MGMT_FILE_ACCESS_HOOK" : "MCUMGR_GRP_FS_FILE_ACCESS_HOOK",
    "FS_MGMT_PATH_SIZE" : "MCUMGR_GRP_FS_PATH_LEN",
    "MCUMGR_CMD_IMG_MGMT" : "MCUMGR_GRP_IMG",
    "IMG_MGMT_USE_HEAP_FOR_FLASH_IMG_CONTEXT" : "MCUMGR_GRP_IMG_USE_HEAP_FOR_FLASH_IMG_CONTEXT",
    "IMG_MGMT_UPDATABLE_IMAGE_NUMBER" : "MCUMGR_GRP_IMG_UPDATABLE_IMAGE_NUMBER",
    "IMG_MGMT_VERBOSE_ERR" : "MCUMGR_GRP_IMG_VERBOSE_ERR",
    "IMG_MGMT_DUMMY_HDR" : "MCUMGR_GRP_IMG_DUMMY_HDR",
    "IMG_MGMT_DIRECT_IMAGE_UPLOAD" : "MCUMGR_GRP_IMG_DIRECT_UPLOAD",
    "IMG_MGMT_REJECT_DIRECT_XIP_MISMATCHED_SLOT" : "MCUMGR_GRP_IMG_REJECT_DIRECT_XIP_MISMATCHED_SLOT",
    "IMG_MGMT_FRUGAL_LIST" : "MCUMGR_GRP_IMG_FRUGAL_LIST",
    "MCUMGR_CMD_OS_MGMT" : "MCUMGR_GRP_OS",
    "MCUMGR_GRP_OS_OS_RESET_HOOK" : "MCUMGR_GRP_OS_RESET_HOOK",
    "OS_MGMT_RESET_MS" : "MCUMGR_GRP_OS_RESET_MS",
    "OS_MGMT_TASKSTAT" : "MCUMGR_GRP_OS_TASKSTAT",
    "OS_MGMT_TASKSTAT_ONLY_SUPPORTED_STATS" : "MCUMGR_GRP_OS_TASKSTAT_ONLY_SUPPORTED_STATS",
    "OS_MGMT_TASKSTAT_MAX_NUM_THREADS" : "MCUMGR_GRP_OS_TASKSTAT_MAX_NUM_THREADS",
    "OS_MGMT_TASKSTAT_THREAD_NAME_LEN" : "MCUMGR_GRP_OS_TASKSTAT_THREAD_NAME_LEN",
    "OS_MGMT_TASKSTAT_SIGNED_PRIORITY" : "MCUMGR_GRP_OS_TASKSTAT_SIGNED_PRIORITY",
    "OS_MGMT_TASKSTAT_STACK_INFO" : "MCUMGR_GRP_OS_TASKSTAT_STACK_INFO",
    "OS_MGMT_ECHO" : "MCUMGR_GRP_OS_ECHO",
    "OS_MGMT_MCUMGR_PARAMS" : "MCUMGR_GRP_OS_MCUMGR_PARAMS",
    "MCUMGR_CMD_SHELL_MGMT" : "MCUMGR_GRP_SHELL",
    "MCUMGR_CMD_SHELL_MGMT_LEGACY_RC_RETURN_CODE" : "MCUMGR_GRP_SHELL_LEGACY_RC_RETURN_CODE",
    "MCUMGR_CMD_STAT_MGMT" : "MCUMGR_GRP_STAT",
    "STAT_MGMT_MAX_NAME_LEN" : "MCUMGR_GRP_STAT_MAX_NAME_LEN",
    "MCUMGR_GRP_ZEPHYR_BASIC" : "MCUMGR_GRP_ZBASIC",
    "MCUMGR_GRP_BASIC_CMD_STORAGE_ERASE" : "MCUMGR_GRP_ZBASIC_STORAGE_ERASE",
    "MGMT_VERBOSE_ERR_RESPONSE" : "MCUMGR_SMP_VERBOSE_ERR_RESPONSE",
    "MCUMGR_SMP_REASSEMBLY_BT" : "MCUMGR_TRANSPORT_BT_REASSEMBLY",
    "MCUMGR_SMP_REASSEMBLY" : "MCUMGR_TRANSPORT_REASSEMBLY",
    "MCUMGR_SMP_REASSEMBLY_UNIT_TESTS" : "MCUMGR_TRANSPORT_REASSEMBLY_UNIT_TESTS",
    "MCUMGR_BUF_COUNT" : "MCUMGR_TRANSPORT_NETBUF_COUNT",
    "MCUMGR_BUF_SIZE" : "MCUMGR_TRANSPORT_NETBUF_SIZE",
    "MCUMGR_BUF_USER_DATA_SIZE" : "MCUMGR_TRANSPORT_NETBUF_USER_DATA_SIZE",
    "MCUMGR_SMP_BT" : "MCUMGR_TRANSPORT_BT",
    "MCUMGR_SMP_BT_AUTHEN" : "MCUMGR_TRANSPORT_BT_AUTHEN",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL_MIN_INT" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL_MIN_INT",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL_MAX_INT" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL_MAX_INT",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL_LATENCY" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL_LATENCY",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL_TIMEOUT" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL_TIMEOUT",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL_RESTORE_TIME" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL_RESTORE_TIME",
    "MCUMGR_SMP_BT_CONN_PARAM_CONTROL_RETRY_TIME" : "MCUMGR_TRANSPORT_BT_CONN_PARAM_CONTROL_RETRY_TIME",
    "MCUMGR_SMP_DUMMY" : "MCUMGR_TRANSPORT_DUMMY",
    "MCUMGR_SMP_DUMMY_RX_BUF_SIZE" : "MCUMGR_TRANSPORT_DUMMY_RX_BUF_SIZE",
    "MCUMGR_SMP_SHELL" : "MCUMGR_TRANSPORT_SHELL",
    "MCUMGR_SMP_SHELL_MTU" : "MCUMGR_TRANSPORT_SHELL_MTU",
    "MCUMGR_SMP_SHELL_RX_BUF_COUNT" : "MCUMGR_TRANSPORT_SHELL_RX_BUF_COUNT",
    "MCUMGR_SMP_UART" : "MCUMGR_TRANSPORT_UART",
    "MCUMGR_SMP_UART_ASYNC" : "MCUMGR_TRANSPORT_UART_ASYNC",
    "MCUMGR_SMP_UART_ASYNC_BUFS" : "MCUMGR_TRANSPORT_UART_ASYNC_BUFS",
    "MCUMGR_SMP_UART_ASYNC_BUF_SIZE" : "MCUMGR_TRANSPORT_UART_ASYNC_BUF_SIZE",
    "MCUMGR_SMP_UART_MTU" : "MCUMGR_TRANSPORT_UART_MTU",
    "MCUMGR_SMP_UDP" : "MCUMGR_TRANSPORT_UDP",
    "MCUMGR_SMP_UDP_IPV4" : "MCUMGR_TRANSPORT_UDP_IPV4",
    "MCUMGR_SMP_UDP_IPV6" : "MCUMGR_TRANSPORT_UDP_IPV6",
    "MCUMGR_SMP_UDP_PORT" : "MCUMGR_TRANSPORT_UDP_PORT",
    "MCUMGR_SMP_UDP_STACK_SIZE" : "MCUMGR_TRANSPORT_UDP_STACK_SIZE",
    "MCUMGR_SMP_UDP_THREAD_PRIO" : "MCUMGR_TRANSPORT_UDP_THREAD_PRIO",
    "MCUMGR_SMP_UDP_MTU" : "MCUMGR_TRANSPORT_UDP_MTU",
}

def process_file(path):
    modified = False
    output = []

    try:
        with open(path) as f:
            lines = f.readlines()

            for line in lines:
                longest = ""
                length = 0
                for m in REPLACEMENTS:
                    if re.match(".*" + m + ".*", line) and len(m) > length:
                        length = len(m)
                        longest = m

                if length != 0:
                    modified = True
                    line = line.replace(longest, REPLACEMENTS[longest])

                output.append(line)

        if modified is False:
            return

        with open(path, "w") as f:
            f.writelines(output)

    except UnicodeDecodeError:
        print(f"Unable to read lines from {path}", file=sys.stderr)
    except Exception as e:
        print(f"Failed with exception {e}", e)

def process_tree(project):
    for p in project.glob("**/*"):
        for fp in FILE_PATTERNS:
            cfp = re.compile(".+/" + fp + "$")
            if re.match(cfp, str(p)) is not None:
                process_file(p)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", "--root", type=Path, required=True, help="Zephyr-based project path"
    )
    args = parser.parse_args()

    process_tree(args.root)
