// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int a3(int i = 3) {
  int * j = new int(2);
  int * k = new int(7);
  std::cout <<  "Ptr:" << j << std::endl;

  return 0;
}


int main()
{
  return a3();
}
