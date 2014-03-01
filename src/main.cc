#include <stdlib.h>
#include <stdio.h>

#include <ctime>

#include "gpio_lib.hh"

#define INPUT_PM1	SUNXI_GPC(19)
#define INPUT_PM25	SUNXI_GPI(20)

int main() {

	if (SETUP_OK != sunxi_gpio_init()) {
		printf("Failed to initialize GPIO: %m\n");
		return -1;
	}

	if (SETUP_OK != sunxi_gpio_set_cfgpin(INPUT_PM1, INPUT)){
		printf("Failed to config GPIO pin\n");
		return -1;
	}

	if (SETUP_OK != sunxi_gpio_set_cfgpin(INPUT_PM25, INPUT)){
		printf("Failed to config GPIO pin\n");
		return -1;
	}

	long long i = 0, cnt_pm1 = 0, cnt_pm25 = 0;
	time_t start_time = time(NULL);
	for (; ; i ++) {
		if (!sunxi_gpio_input(INPUT_PM25))
			cnt_pm25 ++;
		if (!sunxi_gpio_input(INPUT_PM1))
			cnt_pm1 ++;
		if (i % 10000 == 0) {
			printf("%lld,%lld /%lld\r", cnt_pm1, cnt_pm25, i);
			fflush(stdout);
			if ((time(NULL) - start_time) >= 300)
				break;
		}
	}
	printf("\n");
	sunxi_gpio_cleanup();

	return 0;

}


