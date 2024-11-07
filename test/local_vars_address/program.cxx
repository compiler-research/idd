// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int f(int arg1, int arg2) {
#if V1
  int var1 = 1;
  int var2 = 2;
#else
  int var2 = 2;
  int var1 = 1;
#endif
  std::cout << "var1_ptr:" << &var1 << ", var2_ptr:" << &var2 << std::endl;
  return var1 + var2 + arg1 + arg2;
}

int main()
{
  std::cout << "Result:" << f(1, 2) << std::endl;
  return 0;
}
