/*******************************************************

  SLab - Python 
  
  MBED Firmware for Nucleo Boards
  Alternate version for profiling
  
  Program to operate a nucleo board from a PC
  in order to perform measurements.
  
  Desgined for the Nucleo64 F303RE Board

  Commands implemented in version 1
  
  Global
  
  F     : Obtain a string that describes the firmware
  M     : Obtain 4 byte magic code
  I     : Board capabilities identification
  L     : Pin list
  E     : Soft Reset
  
  DC
  
  A + 1 : Read one ADC channel
  D + 3 : Write one DAC channel
  N + 2 : Set number of reads to average

  
  Transient
  
  R + 2 : Set sample time
  S + 4 : Set storage configuration
  Y     : Async read
  G + 3 : Triggered read
  P + 2 : Step response
  
  Wavetable
  
  W + n : Load a wavetable
  w + n : Load a secondary wavetable
  V + 2 : Wave response
  v + 2 : Dual wave response
  X + 3 : Single Wave Response
  Q + 2 : Wave Play
  q + 2 : Dual Wave Play
    
  Digital I/O
  
  H + 2 : dio mode
  J + 2 : dio write
  K + 1 : dio read  
     
Incidences:

  06/04/2017 : Open Drain does not work as expected
               It is currently disabled    
               
  25/10/2017 : v1.1
               Hardware profile lines added
               Improved timings. Minimum sample times:
                 Asyn Read: 1CH (13us) 2CH (33us)  3CH (43us) 4CH (54us)
                 Trig Read: 1CH (13us) 2CH (33us)  3CH (44us) 4CH (54us)
                 Step Resp: 1CH (13us) 2CH (36us)  3CH (46us) 4CH (56us)
                 Wave Resp: 1CH (13us) 2CH (38us)  3CH (47us) 4CH (58us)
                 Dual Wave: 1CH (13us) 2CH (40us)  3CH (50us) 4CH (61us)
                 Sing Wave: 1CH Only (13us)   
                 Wave play: No ADC (11us)  
                 Dual wave play: No ADC (11us)      
     
  10/02/2018 : v1.2  
               Addition of halt button/interrupt
  11/02/2018 : Correction of bug in return code from dualWavePlay             
          
********************************************************/

#include "mbed.h"

/***************** MAIN DEFINES *************************************/

// Version string
#define VSTRING " v1.2"

// Major number version changes when new commands are added
#define VERSION 1

// Uncomment to use hardware profiling during tests
// It should be commented for release versions
//#define USE_PROFILING 1

// Information about the board
#include "Nucleo64-F303RE.h"  // Board 1
//#include "Nucleo32-F303K8.h"  // Board 2
//#include "Nucleo64-L152RE.h"  // Board 3

/******************* OTHER CONSTANTS ******************************/

// Max value in unsigned 16bit as float number
#define MAX16F 65536.0f 

// Special serial codes
#define ACK  181
#define NACK 226
#define ECRC 37

// Codes for transient responses
#define TRAN_OK       0  // Ok
#define TRAN_OVERRUN  1  // Sample overrun
#define TRAN_TIMEOUT  2  // Triggered timeout
#define TRAN_HALT     3  // Halt interrupt generated

// Magic data is different for each firmware
#define MAGIC_SIZE 4
const uint8_t magic[MAGIC_SIZE]={56,41,18,1};

/***************** VARIABLES AND OBJECTS *************************/

Serial pc(SERIAL_TX, SERIAL_RX, 38400);   // Serial link with PC

AnalogIn   ain1(AD1);
AnalogIn   ain2(AD2);
AnalogIn   ain3(AD3);
AnalogIn   ain4(AD4);

AnalogIn   *ainList[NADCS];

AnalogOut  aout1(DA1);   // DAC1
AnalogOut  aout2(DA2);   // DAC2 
#ifdef EXIST_DAC3
AnalogOut  aout3(DA3);   // DAC3 if exists
#endif 

#ifdef EXIST_DIO  // For now, it requires 8 DIO
DigitalInOut dio1(DIO1);
DigitalInOut dio2(DIO2);
DigitalInOut dio3(DIO3);
DigitalInOut dio4(DIO4);
DigitalInOut dio5(DIO5);
DigitalInOut dio6(DIO6);
DigitalInOut dio7(DIO7);
DigitalInOut dio8(DIO8);

DigitalInOut *dioList[NDIO];
#endif

// Sample time period defaults to 1ms
float stime = 0.001;

// Buffer for storage of inputs (in U16)
//uint16_t inBuff[IN_BSIZE];

// Wavetable buffer (in U16)
//uint16_t waveBuff[WSIZE];

// Unified memory buffer
uint16_t buff[BSIZE];

// Start of all buffer sections
uint16_t *wave2buff = NULL;
uint16_t *tranBuff  = NULL;

// DC analog read number of readings
int nread = 10;

// Input configuration
int n_ai = 1;     // Number of analog inputs
int n_di = 0;     // Number of digital inputs (always zero)
int n_s  = 1000;  // Number of samples

// Ticker for readings
Ticker ticR;

// Sample information for ticker
int samples = 0;    // Number of processed samples
int inBuffPos = 0;  // Current buffer position

int presamples;     // Number of samples before trigger
int postsamples;    // Number of samples after trigger
int triggerSample;  // Sample number at trigger point
int samplePhase;    // Sample phase
int currentBsize;   // Current buffer size
int trigger;        // Trigger value
int triggerMode;    // Trigger mode (0 Rise 1 Fall)
int stepValue;      // Value for step analysis

int checkTimeOut;   // Indicates if we check timeout
uint32_t timeOut;   // Timeout for triggered capture

// Global to communicate with ISR ticker
volatile int endTicker = 0;

// Global to check overruns
volatile int overrun = 0;
volatile int overrun_error = 0;
volatile int timeout_error = 0;

int w_s = 0;             // Wavetable size (in samples)
volatile int w_n = 10;   // Number of waves before measurement
volatile int w_pos = 0;  // Current wave position

int w_s2 = 0;            // Secondary wavetable size (in samples)
volatile int w_pos2 = 0; // Current secondary wave position

int infiniteWave = 0;   // Flag for infinite wave play

// Globals for CRC
int crcTx,crcRx;

// Selected ADC for transient
AnalogIn *ain_tran;

// Indicate that board status is at reset condition
int resetState=1;

// Halt interrupt (if enabled)
#ifdef HALT_PIN
InterruptIn haltInt(HALT_PIN);
#endif

// Halt condition flag
volatile int halt = 0;


/****************** HARDWARE PROFILING *********************************/
// Uses GPIO lines to show system activity

#ifdef USE_PROFILING

// Profiling outputs
DigitalOut pro1(PRO1_PIN);
DigitalOut pro2(PRO2_PIN);

#else

#define PRO1_SET    /* No code */
#define PRO1_CLEAR  /* No code */
#define PRO2_SET    /* No code */
#define PRO2_CLEAR  /* No code */ 

#endif //USE_PROFILING

/*********************** SERIAL CODE **********************************/

// Start Tx
// Clears the tx crc
void startTx()
 {
 crcTx = 0;
 }
 
// Send Tx CRC
// Usually that ends transmission
void sendCRC()
 {
 pc.putc(crcTx);
 }     
 
// Send one byte and computes crc
void sendByte(int value)
 {
 pc.putc(value);
 crcTx = crcTx ^ value;    
 }    
 
// Send one uint16 and computes crc
void sendU16(int value)
 {
 int low,high;    
 
 high = value / 256;
 low  = value % 256;
      
 sendByte(low);
 sendByte(high);    
 }    
      
// Send float as mantisa and exponent
void sendMantExp(int mantissa, int exponent)
 {
 sendByte(exponent+128);
 sendU16(mantissa+20000);    
 }     
      
// Send one string and computes crc
void sendString(char *str)
 {
 while (*str)
    {
    sendByte(*str); 
    str++;
    }
 }          

// Start of a Rx reception
void startRx()
 { 
 crcRx = 0;
 }    
 
 
// Get CRC anc check it
// It usually ends the Rx reception
// Returns 1 if CRC is ok, 0 if not
int getAndCheckCRC()
 {
 int crc;
 
 crc = pc.getc();
 if (crc != crcRx) return 0;
 return 1;
 }
 
// Get and check CRC and sends ECRC in case of error
// If no error, don't respond anything
// Returns 1 if CRC is ok, 0 if not
int crcResponse()
 {
 // Check if CRC is ok    
 if (getAndCheckCRC()) return 1;
 
 // If CRC is not ok
 sendByte(ECRC);  
 // End transmission
 sendCRC();
 return 0;    
 }    

   
// Get one byte and computes crc
int getByte()
 {
 int byte;
 
 byte = pc.getc();
 crcRx = crcRx ^byte;
 return byte;   
 }

    
// Get one uint16 and computes crc
int getU16()
 {
 int low, high, value;
 
 low  = getByte();
 high = getByte();
 value = (256 * high) + low;
 
 return value;   
 }   


// Get one float value and computes crc
float getFloat()
 {
 int exp,mant;
 float value; 
 
 exp = getByte() - 128;
 mant = getU16() - 20000;
 
 value = ((float)mant) * pow((float)10.0,(float)exp);
 
 return value;    
 }
   
/*********************** DC CODE ********************************/

// Reads one analog line 1...
// Discards the first reading
// Uses the indicated number of readings
static int analogRead(int line)
 {
 int i,value;    
 uint32_t sum;
 
 sum = 0;
 for(i=0;i<=nread;i++) 
    {
    value=ainList[line-1]->read_u16();
    if (i) sum+=value;
    }    
    
 value = sum/nread;   
      
 return value;     
 }    
 
/********************* TRANSIENT CODE ***************************/ 
 
// Calculates available transize
static inline uint16_t tranBuffSize()
 {
 uint16_t size;
 
 size = BSIZE - w_s - w_s2;   
 return size;  
 }  
 
// Calculates available wave 2 buff size
static inline uint16_t wave2buffSize()
 {
 uint16_t size;
 
 size = BSIZE - w_s;   
 return size;  
 }   
 
// Implements command 'R'
// Sets the sample period time
void setSampleTime()
 {
 //Get sample time
 stime = getFloat();
 
 // End of message, check CRC
 if (!crcResponse()) return;
 
 // Check limits
 if ((stime < MIN_STIME) || (stime > MAX_STIME))
      sendByte(NACK);
      else
      sendByte(ACK);
      
 // End of message
 sendCRC();     
 }    

// Implements command 'S'
// Configure storage
void setStorage()
 {
 int sample_size,size; 
 int error = 0;   
          
 // Get number of analog inputs
 n_ai = getByte();
 if (n_ai > 4) error = 1;
 
 // Get number of digital inputs
 // Not implemented yet
 n_di = getByte();
 if (n_di != 0) error = 1;
 
 // Get the number of samples
 n_s = getU16();
 
 // End of message, check CRC
 if (!crcResponse()) return; 
 
 // Check if it fits the buffer
 if (n_di)
    sample_size = n_ai+1;
    else
    sample_size = n_ai;
    
 size = n_s*sample_size;
 if (size > tranBuffSize()) error = 1;
 
 // Response depending on errors
 if (error)
      sendByte(NACK);
      else
      sendByte(ACK);
      
 // End of message
 sendCRC();          
 }    

// Store analog inputs in circular buffer
static inline int storeAnalog()
 {
 int a1; 
     
 a1 = ain1.read_u16();  
  
 if (n_ai >= 1) tranBuff[inBuffPos++]=a1; 
 if (n_ai >= 2) tranBuff[inBuffPos++]=ain2.read_u16();
 if (n_ai >= 3) tranBuff[inBuffPos++]=ain3.read_u16();
 if (n_ai >= 4) tranBuff[inBuffPos++]=ain4.read_u16();
 
 if (inBuffPos == currentBsize) inBuffPos = 0;
 
 return a1;
 }    

// Dumps the input buffer on serial
void dumpInBuffer()
  {
  int ia,is;    
      
  // Response code
  if (halt)
        {
        sendByte(TRAN_HALT);
        return;
        }
       
  if (overrun_error)
        {
        sendByte(TRAN_OVERRUN);
        return;
        }
        else
        sendByte(TRAN_OK);    
      
  sendByte(n_ai);  // Number of analog    
  sendByte(n_di);  // Number of digital (always zero)
  sendU16(n_s);  // Number of samples
  
  for(ia=0;ia<n_ai;ia++)                // For every analog input
       for(is=0;is<n_s;is++)            // For every sample
       sendU16(tranBuff[is*n_ai+ia]);     // Send it
  }   
  
// Dumps the input buffer on serial
// Overrides the nimber of analog channels and sets it to 1
void dumpInSingleBuffer()
  {
  int is;    
      
  // Response code
  if (halt)
        {
        sendByte(TRAN_HALT);
        return;
        } 
       
  if (overrun_error)
        {
        sendByte(TRAN_OVERRUN);
        return;
        }
        else
        sendByte(TRAN_OK);    
      
  sendByte(1);  // Number of analog is 1   
  sendByte(n_di);  // Number of digital (always zero)
  sendU16(n_s);  // Number of samples
  
  for(is=0;is<n_s;is++)         // For every sample
       sendU16(tranBuff[is]);     // Send it
  }      

/********************* ASYNC READ ***************************/ 

// Hardware profiling operation (if enabled)
//   PRO1 line high during ISR
//   PRO2 line mimics overrun variable

// ISR for the asyncRead function
void asyncReadISR()
 {
 PRO1_SET // Profiling        

 // Store analog data    
 storeAnalog();    
 
 // Increase sample
 samples++;
     
 // Check if we should end
 if (samples >= n_s)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;
    PRO1_CLEAR // Profiling   
    return;
    }   
    
 // Check for halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;
    PRO1_CLEAR // Profiling          
    }       
    
 // Check for overrun
 if (overrun)
    {
    overrun_error = 1;
    }
    
 overrun = 1;  
 
 PRO2_SET    // Profiling
 PRO1_CLEAR            
 }    
 
#ifdef FAST_ADC 
 
// ISR for the asyncRead function
// Optimized timing when only reading one input
// Used only for one input and stime < 25us
void asyncReadSingleISR()
 {
 PRO1_SET // Profiling    
  
 // Direct access to ADC registers 
 ADC1->CR |= ADC_CR_ADSTART;           
 while (!(ADC1->ISR & ADC_ISR_EOC));
 tranBuff[inBuffPos++] = (ADC1->DR)<<4;         
 
 if (inBuffPos == currentBsize) inBuffPos = 0;
 
 // Increase sample
 samples++;
     
 // Check if we should end
 if (samples >= n_s)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;
    PRO1_CLEAR // Profiling   
    return;
    }   
   
 // Check for halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;
    PRO1_CLEAR // Profiling          
    }   
    
 // Check for overrun
 if (overrun)
    {
    overrun_error = 1;
    }
 overrun = 1;    
 
 PRO2_SET    // Profiling
 PRO1_CLEAR         
 }  
 
#endif  //FAST_ADC

// Implements command 'Y'
// Async read
 // This command don't get any parameter
void asyncRead()
 {    
 PRO1_CLEAR  // Reset profiling lines
 PRO2_CLEAR
 
 // Check of CRC
 if (!crcResponse()) return; 
 
 // Send ACK to command
 sendByte(ACK);
 
 // Configure ticker ISR    
 samples = 0;    // Number of processed samples
 inBuffPos = 0;  // Current buffer position
 endTicker = 0;  // Ticker has not ended
 
 currentBsize = n_ai * n_s;        // Current size for buffer
     
 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;   
 PRO2_CLEAR   // Profiling     
     
 #ifdef FAST_ADC     
     
 // Check if we only read one channel and stime is less than 41us
 if ((n_ai==1)&&(stime<25e-6f))
    {
    // Perform a dummy read
    ain1.read_u16();     
    // Programs the ticker for one input optimized ISR version
    ticR.attach(&asyncReadSingleISR,stime);   
    }
   else     
    { 
    // Programs the ticker for several inputs
    ticR.attach(&asyncReadISR,stime);
    }
 
 #else // No FAST_ADC ISR
 
 // Programs the ticker for several inputs
 ticR.attach(&asyncReadISR,stime);
 
 #endif //FAST_ADC
 
 // Wait till end
 while (!endTicker) { overrun = 0; PRO2_CLEAR }
 
 // Return data
 dumpInBuffer();  // Dump data
 
 sendCRC(); // End of Tx 
 }
 
/********************* TRIGGERED READ ***************************/ 
 
// Hardware profiling operation (if enabled)
//   PRO1 line high during ISR
//   PRO2 line mimics overrun variable 
 
// Dumps the input buffer on serial for triggered caputure
void dumpTriggeredInBuffer()
  {
  int ia,is,pos,sample,first;    
      
  presamples = n_s/2;               // Number of samples before trigger
  postsamples = n_s - presamples;   // Number of samples after trigger    
  
  // Response code
  if (halt)
        {
        sendByte(TRAN_HALT);
        return;
        }
  
  if (overrun_error)
        {
        sendByte(TRAN_OVERRUN);
        return;
        }
  
  if (timeout_error)
        {
        sendByte(TRAN_TIMEOUT);    
        return;    
        }
  
  sendByte(TRAN_OK);    
      
  sendByte(n_ai);  // Number of analog    
  sendByte(n_di);  // Number of digital (always zero)
  sendU16(n_s);    // Number of samples
  
  // First sample to send
  first = (triggerSample - presamples + n_s)%n_s;
  
  for(ia=0;ia<n_ai;ia++)                    // For every analog input
       for(is=0;is<n_s;is++)                // For every sample
          {
          sample = (first+is)%n_s;          // Calculate sample
          pos = sample*n_ai+ia;             // Calculate buff position
          sendU16(tranBuff[pos]);            // Send it
          }
  }     
 
// ISR for the triggeredRead function
void triggeredReadISR()
 {
 int a1;    
 
 PRO1_SET
     
 // Store analog data    
 a1 = storeAnalog();    
 
 // Increase sample
 samples++;
 if (samples == n_s) samples = 0;
 
 // Decrease timeout
 timeOut--;
 
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;  
    return;  
    }
 
 // Check phase
 switch(samplePhase)
    {
    case 0: // Prefill of the buffer
      presamples--;
      if (!presamples) samplePhase = 1;
      if (!timeOut)
        {
        // Set error
        timeout_error = 1;
        // Disable ticker
        ticR.detach();     
        // Signal end
        endTicker = 1;
        }
      break;
    case 1: // Wait for trigger precondition
      if (triggerMode == 0) // Rise
         if (a1 < trigger) samplePhase = 2;
      if (triggerMode == 1) // Fall
         if (a1 > trigger) samplePhase = 2;    
      if (!timeOut)
        {
        // Set error
        timeout_error = 1;
        // Disable ticker
        ticR.detach();     
        // Signal end
        endTicker = 1;
        }   
      break;  
    case 2: // Wait for trigger postcondition
      if (triggerMode == 0) // Rise
         if (a1 > trigger)
                     {
                     samplePhase = 3;
                     triggerSample = samples;
                     }
      if (triggerMode == 1) // Fall
         if (a1 < trigger)
                     {
                     samplePhase = 3;
                     triggerSample = samples;
                     }
      if (!timeOut)
        {
        // Set error
        timeout_error = 1;
        // Disable ticker
        ticR.detach();     
        // Signal end
        endTicker = 1;
        }               
      break;
    case 3: // Capture after trigger
      postsamples--;  
      if (!postsamples) 
            {
            // Disable ticker
            ticR.detach();     
            // Signal end
            endTicker = 1;        
            }
      break;    
    } 
    
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 
 PRO2_SET
 PRO1_CLEAR       
 }    
 
#ifdef FAST_ADC 
 
// ISR for the triggeredRead function
// Version optimized for only one channel
// Only used for single channel and stime < 30us
void triggeredReadSingleISR()
 {
 int a1;    
 
 PRO1_SET
     
 // Direct access to ADC registers 
 ADC1->CR |= ADC_CR_ADSTART;           
 while (!(ADC1->ISR & ADC_ISR_EOC));
 a1=(ADC1->DR)<<4;
 tranBuff[inBuffPos++]=a1;  
 
 if (inBuffPos == currentBsize) inBuffPos = 0;   
 
 // Increase sample
 samples++;
 if (samples == n_s) samples = 0;
 
 // Decrease timeout
 timeOut--;
 
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;  
    return;  
    }
 
 // Check phase
 switch(samplePhase)
    {
    case 0: // Prefill of the buffer
      presamples--;
      if (!presamples) samplePhase = 1;
      if (!timeOut)
        {
        // Set error
        timeout_error = 1;
        // Disable ticker
        ticR.detach();     
        // Signal end
        endTicker = 1;
        }
      break;
    case 1: // Wait for trigger precondition
      if (triggerMode == 0) // Rise
         if (a1 < trigger) samplePhase = 2;
      if (triggerMode == 1) // Fall
         if (a1 > trigger) samplePhase = 2;    
      if (!timeOut)
        {
        // Set error
        timeout_error = 1;
        // Disable ticker
        ticR.detach();     
        // Signal end
        endTicker = 1;
        }   
      break;  
    case 2: // Wait for trigger postcondition
      if (triggerMode == 0) // Rise
         if (a1 > trigger)
                     {
                     samplePhase = 3;
                     triggerSample = samples;
                     }
      if (triggerMode == 1) // Fall
         if (a1 < trigger)
                     {
                     samplePhase = 3;
                     triggerSample = samples;
                     }
      if (!timeOut)
        {
        // Set error
        timeout_error = 1;
        // Disable ticker
        ticR.detach();     
        // Signal end
        endTicker = 1;
        }               
      break;
    case 3: // Capture after trigger
      postsamples--;  
      if (!postsamples) 
            {
            // Disable ticker
            ticR.detach();     
            // Signal end
            endTicker = 1;        
            }
      break;    
    } 
    
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 
 PRO2_SET
 PRO1_CLEAR       
 }   
 
#endif //FAST_ADC 
 
// Implements command 'G'
// Triggered read
void triggeredRead()
 {    
 PRO1_CLEAR  // Reset profiling lines
 PRO2_CLEAR
 
 // Get trigger point
 trigger = getU16();
 // Get trigger mode
 triggerMode = getByte();
 // Get timeout in seconds
 timeOut = getByte();
 
 if (timeOut)
    {
    checkTimeOut=1;
    // Convert to samples
    timeOut=int(1.0*timeOut/stime);
    }
    else
    checkTimeOut = 0;
 
 // Erase timeout error
 timeout_error = 0;
 
 // Check of CRC
 if (!crcResponse()) return; 
 
 // Check mode
 if ( (triggerMode != 0) && (triggerMode != 1) )
    {
    sendByte(NACK);
    sendCRC();
    return;
    }
    
 // All ok
 sendByte(ACK);   
 
 // Configure ticker ISR    
 samples = 0;    // Number of processed samples
 inBuffPos = 0;  // Current buffer position
 endTicker = 0;  // Ticker has not ended
 
 presamples = n_s/2;               // Number of samples before trigger
 postsamples = n_s - presamples;   // Number of samples after trigger
 currentBsize = n_ai * n_s;        // Current size for buffer
 
 samplePhase = 0; // First phase: buffer prefill
 
 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;  

 #ifdef FAST_ADC

 // Check if we only read one channel
 if ((n_ai==1)&&(stime<30e-6f))
    {
    // Perform a dummy read
    ain1.read_u16();     
    // Programs the ticker for one input optimized ISR version
    ticR.attach(&triggeredReadSingleISR,stime);   
    }
   else     
    { 
    // Programs the ticker for several inputs
    ticR.attach(&triggeredReadISR,stime);
    }
    
 #else // No FAST_ADC code
 
 // Programs the ticker for several inputs
 ticR.attach(&triggeredReadISR,stime);
 
 #endif //FAST_ADC   
  
 // Wait till end
 while (!endTicker) { overrun = 0; PRO2_CLEAR }
 
 // Return data
 dumpTriggeredInBuffer();  // Dump data
 
 // Send CRC to end Tx
 sendCRC();
 }

/********************* STEP RESPONSE ***************************/

// Hardware profiling operation (if enabled)
//   Not implemented yet

// ISR for the stepResponse function
void stepResponseISR()
 {
 // Store analog data    
 storeAnalog();    
 
 // Increase sample
 samples++;
     
 // Check trigger position
 if (samples == triggerSample) aout1 = stepValue / MAX16F;
     
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;  
    }     
     
 // Check if we should end
 if (samples >= n_s)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;    
    }        
    
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }    

#ifdef FAST_ADC

 // ISR for the stepResponse function
 // Time optimized version
 // Only used for one channel and stime < 30us
 void stepResponseSingleISR()
 {
 // Direct access to ADC registers 
 ADC1->CR |= ADC_CR_ADSTART;           
 while (!(ADC1->ISR & ADC_ISR_EOC));
 tranBuff[inBuffPos++]=(ADC1->DR)<<4;  
 
 if (inBuffPos == currentBsize) inBuffPos = 0;     
 
 // Increase sample
 samples++;
     
 // Check trigger position
 if (samples == triggerSample)
       DAC->DHR12R1 = (stepValue>>4);
     
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;  
    }       
     
 // Check if we should end
 if (samples >= n_s)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;    
    }        
    
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }    
 
#endif //FAST_ADC 

// Implements command 'P'
// Step response
void stepResponse()
 {    
 // Read step value
 stepValue = getU16();
 
 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK); // All Ok
 
 // Configure ticker ISR    
 samples = 0;               // Number of processed samples
 inBuffPos = 0;             // Current buffer position
 endTicker = 0;            // Ticker has not ended
 
 triggerSample = n_s/5;
 
 currentBsize = n_ai * n_s;        // Current size for buffer
     
 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;    
     
 #ifdef FAST_ADC    
     
 // Check if we only read one channel
 if ((n_ai==1)&&(stime<30e-6f))
    {
    // Perform a dummy read
    ain1.read_u16();    
    // Programs the ticker
    ticR.attach(&stepResponseSingleISR,stime);
    }
    else
    {     
    // Programs the ticker
    ticR.attach(&stepResponseISR,stime);
    }
    
 #else // No FAST_ADC code
 
 // Programs the ticker
 ticR.attach(&stepResponseISR,stime);
 
 #endif //FAST_ADC   
 
 // Wait till end
 while (!endTicker) overrun = 0;
 
 // Return data
 dumpInBuffer();  // Dump data
 
 // Send CRC to end Tx
 sendCRC();
 }

/********************* WAVETABLE CODE ***************************/ 

// Load a wavetable
void loadWaveTable()
 {
 int i;    
     
 // Eliminate secondary wavetable
 w_s2 = 0;    
     
 // Get size
 w_s = getU16();
 
 // Check size
 if (w_s > BSIZE) 
    {
    w_s = 0; // Eliminate table
    
    // Calculate new memory configuration
    wave2buff=&buff[w_s];
    tranBuff =&buff[w_s];
 
    sendByte(NACK);
    sendCRC();
    return;    
    }
     
 // Calculate new memory configuration
 wave2buff=&buff[w_s];
 tranBuff =&buff[w_s];
 
 if (w_s > 0) 
   {
   // Load samples
   for(i=0;i<w_s;i++)
      buff[i] = getU16();
   }   

 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK);
    
 sendCRC();   
 }
 
// Load a secondary wavetable
void loadSecondaryWaveTable()
 {
 int i;    
     
 // Get size
 w_s2 = getU16();
 
 // Check size and primary wavetable
 if (w_s2 > wave2buffSize()) 
    {
    w_s2 = 0;
    // Calculate new memory configuration
    tranBuff =&buff[w_s+w_s2];
    
    sendByte(NACK);
    sendCRC();
    return;    
    }
 
 // Calculate new memory configuration
 tranBuff =&buff[w_s+w_s2];
 
 for(i=0;i<w_s2;i++)
    wave2buff[i] = getU16();

 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK);
    
 sendCRC();   
 }
 

/****************** WAVE RESPONSE CODE *************************/ 

// Hardware profiling operation (if enabled)
//    Not implemented

// ISR for the waveResponse function
void waveResponseISR()
 {
 // Write DAC
 aout1 = buff[w_pos++] / MAX16F;    
     
 // Store analog data    
 if (!w_n)
      {
      storeAnalog();    
     
      // Increase sample
      samples++;
     
      // Check if we should end
      if (samples >= n_s)
           {
           // Disable ticker
           ticR.detach();     
           // Signal end
           endTicker = 1;    
           } 
      
      // Check wave rollover
      if (w_pos == w_s) w_pos = 0;        
      }
     else
      {
      // Check wave rollover    
      if (w_pos == w_s)
            {
            w_pos = 0;    
            w_n--;
            }
      }                     
                 
 // Check wave rollover
 // if (w_pos == w_s) w_pos = 0;
       
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;       
    return;
    }          
        
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }    

#ifdef FAST_ADC

// ISR for the waveResponse function
// Time optimized version
// Only used for single ADC and stime < 30us
void waveResponseSingleISR()
 {
 // Write DAC
 DAC->DHR12R1 = (buff[w_pos++]>>4);
     
 // Store analog data    
 if (!w_n)
      {
      // Direct access to ADC registers 
      ADC1->CR |= ADC_CR_ADSTART;           
      while (!(ADC1->ISR & ADC_ISR_EOC));
      tranBuff[inBuffPos++]=(ADC1->DR)<<4;  
 
      if (inBuffPos == currentBsize) inBuffPos = 0;    
     
      // Increase sample
      samples++;
     
      // Check if we should end
      if (samples >= n_s)
           {
           // Disable ticker
           ticR.detach();     
           // Signal end
           endTicker = 1;    
           } 
      
      // Check wave rollover
      if (w_pos == w_s) w_pos = 0;        
      }
     else
      {
      // Check wave rollover    
      if (w_pos == w_s)
            {
            w_pos = 0;    
            w_n--;
            }
      }                     
                 
 // Check wave rollover
 // if (w_pos == w_s) w_pos = 0;
        
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;       
    return;
    }         
        
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }    
 
#endif //FAST_ADC 

// Wave response
void waveResponse()
 {
 // Read number of waves before mesurement    
 w_n = getU16();   

 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK);

 // Configure ticker ISR    
 samples = 0;               // Number of processed samples
 inBuffPos = 0;             // Current buffer position
 endTicker = 0;             // Ticker has not ended
 w_pos = 0;                 // Current wave position 

 currentBsize = n_ai * n_s;        // Current size for buffer
 
 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;
 
 #ifdef FAST_ADC
 
 // Check if we only read one channel
 if ((n_ai==1)&&(stime<30e-6f))
    {
    // Perform a dummy read
    ain1.read_u16();    
    // Programs the ticker
    ticR.attach(&waveResponseSingleISR,stime);
    }
    else
    {    
    // Programs the ticker
    ticR.attach(&waveResponseISR,stime);
    }
    
 #else //No FAST_ADC code
 
 // Programs the ticker
 ticR.attach(&waveResponseISR,stime);
 
 #endif //FAST_ADC   
   
 // Wait till end
 while (!endTicker) overrun = 0;
 
 // Return data
 dumpInBuffer();  // Dump data  
 
 // End sending CRC
 sendCRC(); 
 }    

/*************** DUAL WAVE RESPONSE CODE *************************/ 

// ISR for the dualWaveResponse function
void dualWaveResponseISR()
 {
 // Write DACs
 aout1 = buff[w_pos++] / MAX16F;    
 aout2 = wave2buff[w_pos2++] / MAX16F;
      
 // Store analog data    
 if (!w_n)
      {
      storeAnalog();    
     
      // Increase sample
      samples++;
     
      // Check if we should end
      if (samples >= n_s)
           {
           // Disable ticker
           ticR.detach();     
           // Signal end
           endTicker = 1;    
           } 
      
      // Check wave rollover
      if (w_pos == w_s)   w_pos = 0;
      if (w_pos2 == w_s2) w_pos2 = 0;
      }
     else
      {
      // Check wave rollover    
      if (w_pos == w_s)
            {
            w_pos = 0;    
            w_n--;
            }
      if (w_pos2 == w_s2) w_pos2 = 0;      
      }                     
                 
 // Check wave rollover
 //if (w_pos == w_s) w_pos = 0;
           
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;       
    return;
    }            
           
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }  
 
#ifdef FAST_ADC 
 
// ISR for the dualWaveResponse function
// Time optimized version
// Use only for single ADC read and stime < 35us
void dualWaveResponseSingleISR()
 {
 // Write DACs
 DAC->DHR12R1 = (buff[w_pos++]>>4);
 DAC->DHR12R2 = (wave2buff[w_pos2++]>>4);
     
 // Store analog data    
 if (!w_n)
      {
      // Direct access to ADC registers 
      ADC1->CR |= ADC_CR_ADSTART;           
      while (!(ADC1->ISR & ADC_ISR_EOC));
      tranBuff[inBuffPos++]=(ADC1->DR)<<4;  
 
      if (inBuffPos == currentBsize) inBuffPos = 0;     
     
      // Increase sample
      samples++;
     
      // Check if we should end
      if (samples >= n_s)
           {
           // Disable ticker
           ticR.detach();     
           // Signal end
           endTicker = 1;    
           } 
      
      // Check wave rollover
      if (w_pos == w_s)   w_pos = 0;
      if (w_pos2 == w_s2) w_pos2 = 0;
      }
     else
      {
      // Check wave rollover    
      if (w_pos == w_s)
            {
            w_pos = 0;    
            w_n--;
            }
      if (w_pos2 == w_s2) w_pos2 = 0;      
      }                     
                 
 // Check wave rollover
 //if (w_pos == w_s) w_pos = 0;
           
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;       
    return;
    }            
           
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }     
 
#endif //FAST_ADC 

// Dual wave response
void dualWaveResponse()
 {
 // Read number of primary waves before mesurement    
 w_n = getU16();   

 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK);

 // Configure ticker ISR    
 samples = 0;               // Number of processed samples
 inBuffPos = 0;             // Current buffer position
 endTicker = 0;             // Ticker has not ended
 w_pos = 0;                 // Current wave position 
 w_pos2 = 0;                // Secondary wave position

 currentBsize = n_ai * n_s;        // Current size for buffer
 
 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;    
 
 #ifdef FAST_ADC
 
 // Check if we only read one channel
 if ((n_ai==1)&&(stime<35e-6f))
    {
    // Perform a dummy read
    ain1.read_u16();   
    // Programs the ticker
    ticR.attach(&dualWaveResponseSingleISR,stime); 
    }
    else
    {
    // Programs the ticker
    ticR.attach(&dualWaveResponseISR,stime);
    }
    
 #else //No FAST_ADC code
 
 // Programs the ticker
 ticR.attach(&dualWaveResponseISR,stime);
 
 #endif //FAST_ADC   
   
 // Wait till end
 while (!endTicker) overrun = 0;
 
 // Return data
 dumpInBuffer();  // Dump data  
 
 // End sending CRC
 sendCRC(); 
 }    

/*************** SINGLE WAVE RESPONSE CODE **********************/ 
// Hardware profiling operation (if enabled)
//   PRO1 line high during ISR
//   PRO2 line mimics overrun variable 

// ISR for the singleWaveResponse function
void singleWaveResponseISR()
 {
 int a1;    
     
 PRO1_SET    
    
 // Write DAC1
 aout1 = buff[w_pos++] / MAX16F;   
     
 // Store analog data    
 if (!w_n)
      {
      // Store data  
      // Store data  
      a1 = ain_tran->read_u16();    
      tranBuff[inBuffPos++]=a1;    
     
      // Increase sample
      samples++;
     
      // Check if we should end
      if (samples >= n_s)
           {
           // Disable ticker
           ticR.detach();     
           // Signal end
           endTicker = 1;    
           } 
      
      // Check wave rollover
      if (w_pos == w_s) w_pos = 0;        
      }
     else
      {
      // Check wave rollover    
      if (w_pos == w_s)
            {
            w_pos = 0;    
            w_n--;
            }
      }                     
                 
 // Check wave rollover
 if (w_pos == w_s) w_pos = 0;
        
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;       
    return;
    }     
    
 overrun = 1;  
 
 PRO2_SET
 PRO1_CLEAR
 }   

#ifdef FAST_ADC

// ISR for the singleWaveResponse function
// Time optimized version
// Only used for stime < 30us
void singleWaveResponseFastISR()
 {
 int a1;    
     
 PRO1_SET    
    
 // Write DAC1
 DAC->DHR12R1 = (buff[w_pos++]>>4);  /* New faster code */
     
 // Store analog data    
 if (!w_n)
      {
      // Store data  
      // Direct access to registers
      ADC1->CR |= ADC_CR_ADSTART;           
      while (!(ADC1->ISR & ADC_ISR_EOC));
      a1 = ADC1->DR;
      tranBuff[inBuffPos++]=a1<<4;    
     
      // Increase sample
      samples++;
     
      // Check if we should end
      if (samples >= n_s)
           {
           // Disable ticker
           ticR.detach();     
           // Signal end
           endTicker = 1;    
           } 
      
      // Check wave rollover
      if (w_pos == w_s) w_pos = 0;        
      }
     else
      {
      // Check wave rollover    
      if (w_pos == w_s)
            {
            w_pos = 0;    
            w_n--;
            }
      }                     
                 
 // Check wave rollover
 if (w_pos == w_s) w_pos = 0;
    
 // Check halt
 if (halt)
    {
    // Disable ticker
    ticR.detach();     
    // Signal end
    endTicker = 1;       
    return;
    }     
        
 // Check for overrun
 if (overrun)
    overrun_error = 1;
      
 overrun = 1;  
 
 PRO2_SET
 PRO1_CLEAR
 }  
 
#endif //FAST_ADC 

// Select analog channel
// In case of error, closes the communication and returns 0
// If all is ok, returns 1
int selectTranChannel(int channel)
 {
 if ((channel<0) || (channel>4))
          {
          sendByte(NACK);
          sendCRC();
          return 0;
          } 
          
 switch(channel)         
    {
    case 1:
        ain_tran=&ain1;
        break;
    case 2:
        ain_tran=&ain2;
        break;
    case 3:
        ain_tran=&ain3;
        break;
    case 4:
        ain_tran=&ain4;
        break;                        
    }
    
 return 1;   
 }    

// Single Wave response
void singleWaveResponse()
 {
 int channel;  
 
 PRO1_CLEAR // Reset profile lines
 PRO2_CLEAR  
     
 // Read channel to read    
 channel = getByte();   
          
 // Read number of waves before mesurement    
 w_n = getU16();   

 // Check of CRC
 if (!crcResponse()) return; 
 
 // Configure the input channel
 if (!selectTranChannel(channel)) return;
 
 // Dummy read
 ain_tran->read_u16();

 // Send ACK
 sendByte(ACK);

 // Configure ticker ISR    
 samples = 0;               // Number of processed samples
 inBuffPos = 0;             // Current buffer position
 endTicker = 0;             // Ticker has not ended
 w_pos = 0;                 // Current wave position 

 currentBsize = n_s;        // Current size for buffer
 
 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;    
 
 #ifdef FAST_ADC
 
 if (stime < 30e-6f)
     {
     // Programs the ticker with fast version
     ticR.attach(&singleWaveResponseFastISR,stime);
     }
     else
     {    
     // Programs the ticker with normal version
     ticR.attach(&singleWaveResponseISR,stime);
     }
     
 #else //No FAST_ADC code
 
 // Programs the ticker with normal version
 ticR.attach(&singleWaveResponseISR,stime);
 
 #endif //FAST_ADC    
   
 // Wait till end
 while (!endTicker) { overrun = 0; PRO2_CLEAR }
 
 // Return data
 dumpInSingleBuffer();  // Dump data  
 
 // End sending CRC
 sendCRC(); 
 }    

/****************** WAVE PLAY CODE *************************/ 

// ISR for the wavePlay function
void wavePlayISR()
 {
 // Write DAC (Old code)
 // aout1 = buff[w_pos++] / MAX16F;    
 
  // Write DACs (New faster code)
 DAC->DHR12R1 = (buff[w_pos++]>>4);
              
 // Check wave rollover    
 if (w_pos == w_s)
     {
     w_pos = 0;   
     if (!infiniteWave)
        { 
        w_n--;
        if (w_n <= 0)
             {
             // Disable ticker
             ticR.detach();     
             // Signal end
             endTicker = 1;     
             return;
             }
        }     
     }
     
 // Check for halt
 if (halt)
      {
      // Disable ticker
      ticR.detach();     
      // Signal end
      endTicker = 1;     
      return;    
      }    
        
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }    

// Wave Play
void wavePlay()
 {
 PRO1_SET
 // Read number of waves to send    
 infiniteWave = 0;
 w_n = getU16();  
 if (w_n==0) 
       infiniteWave = 1; 

 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK);

 // Configure ticker ISR    
 endTicker = 0;             // Ticker has not ended
 w_pos = 0;                 // Current wave position 

 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;    
 
 // Programs the ticker
 ticR.attach(&wavePlayISR,stime);
   
 // Wait till end
 while (!endTicker) overrun = 0;
 
 PRO1_CLEAR
 
 // Response code
 if (halt)
    sendByte(TRAN_HALT);
    else    
     if (overrun_error)
        sendByte(TRAN_OVERRUN);
        else
        sendByte(TRAN_OK);  
 
 // End sending CRC
 sendCRC(); 
 }    

/****************** DUAL WAVE PLAY CODE *************************/ 

// ISR for the dualWavePlay function
void dualWavePlayISR()
 {
 // Write DAC (Old code)
 //aout1 = buff[w_pos++] / MAX16F; 
 //aout2 = wave2buff[w_pos2++] / MAX16F; 
 
 // Write DACs (New faster code)
 DAC->DHR12R1 = (buff[w_pos++]>>4);
 DAC->DHR12R2 = (wave2buff[w_pos2++]>>4);
              
 // Check primary wave rollover    
 if (w_pos == w_s)
     {
     w_pos = 0;    
     if (!infiniteWave)
        {
        w_n--;
        if (w_n <= 0)
             {
             // Disable ticker
             ticR.detach();     
             // Signal end
             endTicker = 1;     
             }
        }     
     }
     
 // Check for secondary wave rollover
 if (w_pos2 == w_s2) w_pos2 = 0;   
 
 // Check for halt
 if (halt)
      {
      // Disable ticker
      ticR.detach();     
      // Signal end
      endTicker = 1;     
      return;    
      }  
        
 // Check for overrun
 if (overrun)
    overrun_error = 1;
    
 overrun = 1;   
 }    

// Dual Wave Play
void dualWavePlay()
 {
 // Read number of waves to send    
 infiniteWave = 0;
 w_n = getU16();  
 if (w_n==0) 
       infiniteWave = 1;  

 // Check of CRC
 if (!crcResponse()) return; 
 
 sendByte(ACK);

 // Configure ticker ISR    
 endTicker = 0;             // Ticker has not ended
 w_pos =  0;                // Current primary wave position 
 w_pos2 = 0;                // Current secondary wave position

 // Clear overrun variables
 overrun_error = 0;
 overrun = 0;    
 
 // Programs the ticker
 ticR.attach(&dualWavePlayISR,stime);
   
 // Wait till end
 while (!endTicker) overrun = 0;
 
 // Response code
 if (halt)
    sendByte(TRAN_HALT);
    else
      if (overrun_error)
        sendByte(TRAN_OVERRUN);
        else
        sendByte(TRAN_OK);  
 
 // End sending CRC
 sendCRC(); 
 }    

/***************** DC DIGITAL IO *********************************/

// Digital IO mode
void dioMode()
 {
 int line,mode,error; 
  
 // Read line to configure 
 line = getByte(); 
     
 // Read mode to set
 mode = getByte();
 
 // Check of CRC
 if (!crcResponse()) return; 
 
 // No error for now
 error = 0;
 
 // Check line number
 if ((line <= 0)||(line > NDIO)) error = 1;
 
 // Set dio mode
 if (!error)
    switch(mode)
        {
        case 10: 
           dioList[line-1]->input();
           dioList[line-1]->mode(PullNone);
           break;
        case 11: 
           dioList[line-1]->input();        
           dioList[line-1]->mode(PullUp);
           break;  
        case 12: 
           dioList[line-1]->input();
           dioList[line-1]->mode(PullDown);
           break;                        
        case 20: 
           dioList[line-1]->mode(PullNone);        
           dioList[line-1]->output();        
           break;  
//        case 21: 
//           dioList[line-1]->mode(OpenDrain);        
//           dioList[line-1]->output();        
//           break; 
        default:
           error = 1;
           break;                             
        }
        
 if (error)
    sendByte(NACK);
    else
    sendByte(ACK);     
 
 // End sending CRC
 sendCRC(); 
 }
 
// Digital Write
void dioWrite()
 {
 int line,value; 
  
 // Read line to write 
 line = getByte(); 
     
 // Value to set
 value = getByte();
 
 // Check of CRC
 if (!crcResponse()) return; 
 
 // Check line number
 if ((line <= 0)||(line > NDIO)) 
     {
     sendByte(NACK);
     sendCRC();
     return;
     }
 
 // Set dio value
 dioList[line-1]->write(value);

 // Send ACK and CRC
 sendByte(ACK);     
 sendCRC(); 
 } 
 
// Digital Read
void dioRead()
 {
 int line,value; 
  
 // Read line to read
 line = getByte(); 
 
 // Check of CRC
 if (!crcResponse()) return; 
 
 // Check line number
 if ((line <= 0)||(line > NDIO)) 
     {
     sendByte(NACK);
     sendCRC();
     return;
     }
 
 // Send ACK
 sendByte(ACK);
 
 // Read and send dio value
 value=dioList[line-1]->read();
 if (value)
    sendByte(1);
    else
    sendByte(0);
 
 // Send CRC     
 sendCRC(); 
 }  

/***************** MAIN LOOP CODE ********************************/

// Soft reset
// Put the system in default reset state
void softReset(void)
 {
 int i;    
     
 // Sample time period defaults to 1ms
 stime = 0.001;
 
 // Set number of DC readings to 10
 nread = 10;
 
 // Input configuration
 n_ai = 1;     // Number of analog inputs
 n_di = 0;     // Number of digital inputs (always zero)
 n_s  = 1000;  // Number of samples
 
 // Eliminate wavetables
 w_s =  0;  
 w_s2 = 0;
 
 // Initialize unified memory
 wave2buff = buff;
 tranBuff  = buff;  
 
 // Set DACs to zero
 aout1 = 0.0;
 aout2 = 0.0; 
 
 // Fill ain list
 ainList[0]=&ain1;
 ainList[1]=&ain2;
 ainList[2]=&ain3;
 ainList[3]=&ain4;
 
 // Configure DIO
 #ifdef EXIST_DIO
 // Setup dioList
 dioList[0]=&dio1;
 dioList[1]=&dio2;
 dioList[2]=&dio3;
 dioList[3]=&dio4;
 dioList[4]=&dio5;
 dioList[5]=&dio6;
 dioList[6]=&dio7;
 dioList[7]=&dio8;
 // Default configuration
 for(i=0;i<NDIO;i++)
    {
    dioList[i]->mode(PullNone);
    dioList[i]->input();    
    }    
 #endif
 }


// Halt funcion
// Called when the halt interrupt is generated
void haltFunction()
 {
 halt=1; // Just turn on the halt flag    
 }

// Process one character received from the PC
void process(int car)
 {
 int i;
 uint16_t value;
  
 // Initialize Tx CRC
 startTx();
    
 switch(car)
    {
    case 'F': // Get firmware string
        sendString(BSTRING);
        sendString(VSTRING);
        sendString("\n\r");
        break;
    case 'M': // Get magic
        // Check CRC of command. Returns 1 if Ok
        // On error Sends ECRC + CRC and return 0
        if (!crcResponse()) return;
        sendByte(ACK);
        // Send magic
        for(i=0;i<MAGIC_SIZE;i++)
            sendByte(magic[i]);
        // Send CRC
        sendCRC();
        break; 
    case 'I': // Get board capabilities
        // Check CRC of command. Returns 1 if Ok
        // On error Sends ECRC + CRC and return 0
        if (!crcResponse()) return;
        sendByte(ACK);
            
        sendByte(NDACS);                //  1
        sendByte(NADCS);                //  2
        sendU16(BSIZE);                 //  4 Buffer
        sendMantExp(MAX_S_M,MAX_S_E);   //  7
        sendMantExp(MIN_S_M,MIN_S_E);   // 10
        sendMantExp(VDD_M,VDD_E);       // 13
        sendMantExp(MAX_SF_M,MAX_SF_E); // 16
        sendMantExp(VREF_M,VREF_E);     // 29
        sendByte(DAC_BITS);             // 20
        sendByte(ADC_BITS);             // 21
        sendByte(NDIO);                 // 22
        sendByte(resetState);           // 23
        
        // Send CRC
        sendCRC();
        break;
    case 'L' : // Send pin list
        // Check CRC of command. Returns 1 if Ok
        // On error Sends ECRC + CRC and return 0
        if (!crcResponse()) return;
        sendByte(ACK);
        
        sendString(PIN_LIST);
        
        // Send CRC
        sendCRC();        
        break;
        
    
    case 'A' : // ADC Read
        i = getByte();   // Channel to read
        // Check CRC of command. Returns 1 if Ok
        // On error Sends ECRC + CRC and return 0
        if (!crcResponse()) return;   
             
        /*     
        switch(i)
            {
            case 1:
               value = ain1.read_u16();  // Two reads
               value = ain1.read_u16(); 
               break;  
            case 2:
               value = ain2.read_u16();  // Two reads
               value = ain2.read_u16(); 
               break; 
            case 3:
               value = ain3.read_u16();  // Two reads
               value = ain3.read_u16(); 
               break; 
            case 4:
               value = ain4.read_u16();  // Two reads
               value = ain4.read_u16(); 
               break;  
            default:
               sendByte(NACK);
               sendCRC();
               return;                                              
            }  
        */
        if ((i<1)||(i>NADCS))
            {
            sendByte(NACK);
            sendCRC();
            return;     
            }
            
        value = analogRead(i);    
               
        sendByte(ACK);    
        sendU16(value);
        sendCRC();
        break;        
    
    case 'D' : // DAC Write
        i = getByte();          // Channel to write
        value = getU16();       // Read value to set
        // Check CRC of command. Returns 1 if Ok
        // On error Sends ECRC + CRC and return 0
        if (!crcResponse()) return;          
        switch(i)
            {
            case 1: 
               aout1 = value / MAX16F;   // Scale to float and send
               break;
            case 2:
               aout2 = value / MAX16F;   // Scale to float and send
               break;
            #ifdef EXIST_DAC3   
            case 3:
               aout3 = value / MAX16F;   // Scale to float and send
               break;          
            #endif   
            default:
               sendByte(NACK);
               sendCRC();
               return;                
            }  
        sendByte(ACK);    
        sendCRC();     
        resetState=0;  // State change         
        break;    
                          
    case 'R': // Set sample period time
        setSampleTime();
        resetState=0;  // State change
        break;  
    case 'S': // Set Storage
        setStorage();
        resetState=0;  // State change
        break;      
    case 'Y': // Async Read
        asyncRead();
        break;
    case 'G': // Triggered Read
        triggeredRead();
        break;        
    case 'P': // Step response
        stepResponse();
        break;    
        
    case 'W': // Load wavetable
        loadWaveTable();
        resetState=0;  // State change
        break;  
    case 'w': // Load secondary wavetable
        loadSecondaryWaveTable();
        resetState=0;  // State change
        break;         
    case 'V': // Wave response
        waveResponse();
        break;  
    case 'v': // Dual wave response
        dualWaveResponse();
        break;          
    case 'X': // Single Wave response
        singleWaveResponse();
        break; 
    case 'Q': // Wave Play
        wavePlay();
        break;  
    case 'q': // Wave Play
        dualWavePlay();
        break;                 
        
    case 'E': // Soft Reset
        if (!crcResponse()) return;
        
        softReset();
        resetState=1;  // Return to reset state
    
        sendByte(ACK);    
        sendCRC();
        break;   
        
    case 'H': // DIO mode
        dioMode();
        resetState=0;  // State change
        break;  
    case 'J': // DIO Write
        dioWrite();
        resetState=0;  // State change
        break;    
    case 'K': // DIO Read
        dioRead();
        break;   
        
    case 'N': // Number of reads in DC
        value = getU16();             // Read value to set
        if (!crcResponse()) return;   // Check CRC
        if (value==0) value=1;        // At least it shall be one
        nread = value;
        sendByte(ACK);                // Send ACK and CRC
        sendCRC();    
        resetState=0;  // State change          
        break;                          
    
    default:
        // Unknown command
        sendByte(NACK);
        sendCRC();    
        break;             
    }     
 }    

int main() 
 {
 int car;
 
 // Generate soft reset
 softReset();
 
 pc.printf("%s%s\n\r",BSTRING,VSTRING);

 // Reset profile lines (if enabled)
 PRO1_CLEAR
 PRO2_CLEAR
 
 // Program halt interrupt (if enabled)
 #ifdef HALT_PIN
   #ifdef HALT_RISING
   haltInt.rise(&haltFunction);
   #else
   haltInt.fall(&haltFunction);
   #endif
 #endif
 
 // New ADC code
 //adc_init();

 // Loop that processes each received char
 while(1) 
    {
    startRx();        // Init Rx CRC
    car = getByte();  // Get command
    halt = 0;         // Remove halt condition if present
    process(car);     // Process command
    }
 }

