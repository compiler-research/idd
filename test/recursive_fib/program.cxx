// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int fib(int x) {
#if V1
  if (x < 2) {
    return x;
  }
#else
  if (x <= 1) {
    return 1;
  }
#endif
  return (fib(x - 1) + fib(x - 2));
}

int main()
{
  for (int i = 0; i <= 5; i++)
    std::cout << "Result fib(" << i << "):" << fib(i) << std::endl;
  return 0;
}
