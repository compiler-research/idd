// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int f(int arg1, int arg2) {
#if V2
  int i;
#endif

  int var1 = arg1 + 1;
  int var2 = arg2 + 2;

#if V1
  return var1 + var2;
#else
  int result;
  for (i = 0; i < 5; i++) {
    result = var1 + var2;
  }

  return result;
#endif

}

int main()
{
  std::cout << "Result:" << f(1, 2) << std::endl;
  return 0;
}
