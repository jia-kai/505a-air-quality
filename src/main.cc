/*
 * $File: main.cc
 * $Date: Sun Mar 02 13:08:49 2014 +0800
 * $Author: jiakai <jia.kai66@gmail.com>
 */


#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <ctime>
#include <cstring>

#include <unistd.h>
#include <signal.h>

#include "gpio_lib.hh"

#define INPUT_PM1	SUNXI_GPC(19)
#define INPUT_PM25	SUNXI_GPI(20)

typedef uint64_t nsec_time_t;

static nsec_time_t get_current_time() {
	timespec t;
	if (clock_gettime(CLOCK_MONOTONIC_RAW, &t)) {
		fprintf(stderr, "failed to get time: %m\n");
		exit(-1);
	}
	return nsec_time_t(t.tv_sec) * 1000000000 + t.tv_nsec;
}

class PWMDecoder {
	nsec_time_t m_tot_neg = 0, m_negedge_time = 0;
	int m_prev_v = 1, m_nr_posedge = 0;
	
	public:
		void feed(int v) {
			if (!m_prev_v && v) {
				m_prev_v = 1;
				m_tot_neg += get_current_time() - m_negedge_time;
				m_nr_posedge ++;
			} else if (m_prev_v && !v) {
				m_prev_v = 0;
				m_negedge_time = get_current_time();
			}
		}

		nsec_time_t get_tot_neg() const {
			return m_tot_neg;
		}

		int get_nr_posedge() const {
			return m_nr_posedge;
		}
};

static nsec_time_t start_time;
static PWMDecoder pwm1, pwm25;

static void alarm_handler(int) {
	pwm1.feed(1);
	pwm25.feed(1);
	auto tot_time = get_current_time() - start_time,
		 pm1 = pwm1.get_tot_neg(),
		 pm25 = pwm25.get_tot_neg();
	printf("%.8f\n%.8f\n%.3lf %.3lf %.3lf\n%d %d\n",
			double(pm1) / tot_time,
			double(pm25) / tot_time,
			pm1 * 1e-9, pm25 * 1e-9, tot_time * 1e-9,
			pwm1.get_nr_posedge(), pwm25.get_nr_posedge());
	sunxi_gpio_cleanup();
	exit(0);
}

static void setup_sighandler() {
	struct sigaction sa;
	memset(&sa, 0, sizeof(sa));
	sa.sa_handler = alarm_handler;
	if (sigaction(SIGALRM,  &sa, nullptr)) {
		fprintf(stderr, "failed to set handler: %m\n");
		exit(-1);
	}
}

int main() {
	if (SETUP_OK != sunxi_gpio_init()) {
		fprintf(stderr, "failed to initialize GPIO: %m\n");
		return -1;
	}

	if (SETUP_OK != sunxi_gpio_set_cfgpin(INPUT_PM1, INPUT)){
		fprintf(stderr, "failed to config GPIO INPUT_PM1\n");
		return -1;
	}

	if (SETUP_OK != sunxi_gpio_set_cfgpin(INPUT_PM25, INPUT)){
		fprintf(stderr, "failed to config GPIO INPUT_PM25\n");
		return -1;
	}

	setup_sighandler();
	alarm(30);

	start_time = get_current_time();

	for (; ; ) {
		pwm1.feed(sunxi_gpio_input(INPUT_PM1));
		pwm25.feed(sunxi_gpio_input(INPUT_PM25));
	}
}


// vim: syntax=cpp11.doxygen foldmethod=marker foldmarker=f{{{,f}}}
