// thread macros to enable windows/posix build
#ifdef _WIN32
  #include "windows.h"
  typedef HANDLE THREAD_ID;
  // FIXME better way to do this?
  typedef struct _ThreadStartParams 
  {
      void *(*func)(void *);
      void *data;
  } ThreadStartParams;
  DWORD start_thread(void *start_params)
  {
    ThreadStartParams *params = (ThreadStartParams *)start_params;
    params->func(params->data);
    return 1;
  }
  int create_thread(THREAD_ID *id, void *(*func)(void *), void *data) {
    ThreadStartParams params;
    params.func = func;
    params.data = data;
	  *id = CreateThread(0, 0, start_thread, &params, 0, NULL);
	  if (id == NULL) return -1;
	  else return 0;
  }
  int join_thread(THREAD_ID id) {
	  DWORD ret = WaitForSingleObject(id, INFINITE);
	  if (ret == WAIT_FAILED) return -1;
	  else return 0;
  }
#else
  #include <pthread.h>
  typedef pthread_t THREAD_ID;
  int create_thread(THREAD_ID *id, void *(*func)(void *), void *data) {
	  return pthread_create(id, NULL, func, data);
  }
  int join_thread(THREAD_ID id) {
	  return pthread_join(id, NULL);
  }
#endif