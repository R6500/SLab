/***********************************************************************

   Header file for the Nucleo64 F303RE Board 

MBED page for the board:
https://os.mbed.com/platforms/ST-Nucleo-F303RE/

Basic requirements for a board are:
  MBED Compatible
  2 DACs or more
  4 ADCs or more
That includes the following Nucleo Boards

 Board           DACs Flash  RAM    
 Nucleo64-F303RE  2*  512k   64k + 16k     (This board)
 Nucleo64-L152RE  2*  512k   80k
 Nucleo32-F303K8  3   64k    12k + 4k    
 Nucleo64-F072RB  2   128k   16k
 Nucleo64-F091RC  2   256k   32k
 Nucleo64-F334R8  3   64k    12k + 4k
 Nucleo64-F446RE  2   512k   128k
 Nucleo64-L073RZ  2   192k   20k
 Nucleo64-L476RG  2   1M     128k

(*) In DACs mean that one DAC has reduced range because
    it is connected to the board LCD

It seems that the DAC set value is more precise than
the ADC. It is recommended to calibrate ADC against DAC.

History:

  2017/02/23 : First version
  2017/10/26 : Updated for v1.1 of cpp file
   
**********************************************************************/   
   
#define BSTRING  "Nucleo64-F303RE MBED SLab"   

#define F_SIZE  512
#define R_SIZE   64

// ADCs

#define AD1 A0
#define AD2 A1
#define AD3 A4
#define AD4 A5

#define FAST_ADC // Optimized code for single readings

// DACs
#define DA1    A2
#define DA2    D13
//#define EXIST_DAC3

// Digital I/O
#define EXIST_DIO
#define DIO1 D2
#define DIO2 D3
#define DIO3 D4
#define DIO4 D5
#define DIO5 D6
#define DIO6 D7
#define DIO7 D8
#define DIO8 D9

// Board capabilities implemented in firmware
#define NDACS       2           // Number of DACs
#define NADCS       4           // Number of ADCs
#define BSIZE       20000       // Unified buffer size (in samples)
#define MAX_STIME   100.0f      // Maximum sample period is 100s
#define MAX_S_M     100         //   Mantissa
#define MAX_S_E     0           //   Exponent
#define MIN_STIME   0.000001f   // Minimum sample period is 1us
#define MIN_S_M      1          //   Mantissa
#define MIN_S_E     -6          //   Exponent
#define VDD_M       33          //   Vdd Mantissa
#define VDD_E       -1          //       Exponent
#define VREF_M      33          //   Vref Mantissa
#define VREF_E      -1          //        Exponent
#define DAC_BITS    12          // Number of DAC bits
#define ADC_BITS    12          // Number of ADC bits
#define MAX_SF      38000       // Maximum sample freq. for f response
#define MAX_SF_M    38          //   Mantissa
#define MAX_SF_E     3          //   Exponent
#define NDIO         8          // Number of digital I/O

// Delay between setting DAC and reading ADC
// Removed as is not usefull enough
//#define DELAY_M      9          //   Mantissa
//#define DELAY_E     -6          //   Exponent

// List of DAC and ADC pins
#define PIN_LIST "A2|D13|A0|A1|A4|A5|D2|D3|D4|D5|D6|D7|D8|D9|$"

// HALT signal
#define HALT_PIN   USER_BUTTON
//#define HALT_RISING  // Interrupt is on falling

// Hardware profiling defines
#ifdef USE_PROFILING

// Profiling pins to be delared as outputs at main()
#define PRO1_PIN   PC_4
#define PRO2_PIN   PB_13

// Profiling code
// Code to set or clear each profile line
// They use low level calls to minimize effect on profiled code
#define PRO1_SET   GPIOC->BSRR = 1<<4;
#define PRO1_CLEAR GPIOC->BSRR = 1<<(16+4);
#define PRO2_SET   GPIOB->BSRR = 1<<13;
#define PRO2_CLEAR GPIOB->BSRR = 1<<(16+13);

#endif //USE_PROFILING
