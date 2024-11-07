// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int f(int arg1) {
  if (arg1 == 0)
#if V1
    return 1;
#else
    return 0;
#endif
  else
    return arg1 * f(arg1 - 1);
}

int main()
{
  std::cout << "Result:" << f(5) << std::endl;
  return 0;
}
