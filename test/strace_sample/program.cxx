// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <stdio.h>
#include <unistd.h>

void file_open()
{
    char str[30];
#if V1
    FILE *fp = fopen("/tmp/strace_sample", "r");
#else
    FILE *fp = fopen("strace_sample", "r");
#endif
    fgets(str, 5, fp);
    fclose(fp);
}

int main() {
  file_open();
  return 0;
}
