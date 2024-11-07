// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int f(int arg1, int arg2) {
  int var1 = 1;
#if V1
  int var2 = 2;
#else
  int var2 = 3;
#endif
  return arg1 + arg2 + var1 + var2;
}

int main()
{
  std::cout << "Result:" << f(1, 2) << std::endl;
  return 0;
}
