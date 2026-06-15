#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

int main(void)
{
    printk("BOOT OK\r\n");
    printk("Board: nrf52dk/nrf52832\r\n");
    printk("Firmware CI PoC started\r\n");

    while (1) {
        printk("Heartbeat\r\n");
        k_sleep(K_SECONDS(5));
    }

    return 0;
}
