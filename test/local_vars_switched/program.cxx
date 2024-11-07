//g++ -DV1 -o a/program.out -xc++ -g program.cxx
//g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int a(int arg1, int arg2) {
#if V1
  int a_var1 = 1;
  int a_var2 = 2;
#else
  int a_var2 = 2;
  int a_var1 = 1;
#endif
  return a_var1 + a_var2 + arg1 + arg2;
}

int main()
{
  std::cout <<  "Result:" << a(1, 2) << std::endl;
  return a(1, 2);
}
