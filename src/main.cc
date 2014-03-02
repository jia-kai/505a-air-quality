/*
 * $File: main.cc
 * $Date: Sun Mar 02 20:42:43 2014 +0800
 * $Author: jiakai <jia.kai66@gmail.com>
 */


#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <ctime>
#include <cstring>

#include <unistd.h>
#include <signal.h>
#include <sched.h>
#include <sys/time.h>
#include <sys/resource.h>

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
static uint64_t total_nr_sample = 0;

static void alarm_handler(int) {
	pwm1.feed(1);
	pwm25.feed(1);
	auto tot_time = get_current_time() - start_time,
		 pm1 = pwm1.get_tot_neg(),
		 pm25 = pwm25.get_tot_neg();
	printf("%.8f\n%.8f\n"
			"measured time: %.3lf %.3lf %.3lf\n"
			"nr_posedge: %d %d\n"
			"avg sample time: %.2lfs/%llu = %.5lfms\n",
			double(pm1) / tot_time,
			double(pm25) / tot_time,
			pm1 * 1e-9, pm25 * 1e-9, tot_time * 1e-9,
			pwm1.get_nr_posedge(), pwm25.get_nr_posedge(),
			tot_time * 1e-9, (unsigned long long)total_nr_sample,
			tot_time / total_nr_sample * 1e-6);
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

static void setup_sched() {
	struct sched_param param;
	memset(&param, 0, sizeof(param));
	param.sched_priority = 99;
	if (sched_setscheduler(0, SCHED_FIFO, &param)) {
		fprintf(stderr, "failed to set to SCHED_FIFO: %m\n");
		exit(-1);
	}
	if (setpriority(PRIO_PROCESS, 0, -20)) {
		fprintf(stderr, "failed to set to setpriority: %m\n");
		exit(-1);
	}

	cpu_set_t cpu;
	CPU_ZERO(&cpu);
	CPU_SET(1, &cpu);
	if (sched_setaffinity(0, sizeof(cpu), &cpu)) {
		fprintf(stderr, "failed to set to setaffinity: %m\n");
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
	setup_sched();
	alarm(30);

	start_time = get_current_time();

	for (; ; total_nr_sample ++) {
		pwm1.feed(sunxi_gpio_input(INPUT_PM1));
		pwm25.feed(sunxi_gpio_input(INPUT_PM25));
	}
}


// vim: syntax=cpp11.doxygen foldmethod=marker foldmarker=f{{{,f}}}
