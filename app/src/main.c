#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include "app_version.h"

int main(void)
{
    printk("BOOT OK\r\n");
    printk("Firmware version: %s\r\n", FW_VERSION);
    printk("Git commit: %s\r\n", FW_GIT_COMMIT);
    printk("Git ref: %s\r\n", FW_GIT_REF);
    printk("Board: %s\r\n", FW_BOARD);
    printk("Build time: %s\r\n", FW_BUILD_TIME);
    printk("Firmware CI PoC started\r\n");

    while (1) {
        printk("Heartbeat\r\n");
        k_sleep(K_SECONDS(5));
    }

    return 0;
}
