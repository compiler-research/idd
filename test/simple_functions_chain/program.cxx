// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

int c(int arg1, int arg2) {
  int c_var1 = 100;
  int c_var2;
#if V1
  c_var2 = 2100;
#else
  c_var2 = 2000;
#endif
  int c_var3 = 300;
  int c_var4 = 400;
  int c_var5 = 500;
  return c_var4 + c_var5;
}

int b(int arg1, int arg2) {
  int b_var1 = 10;
  int b_var2;
#if V1
  b_var2 = 210;
#else
  b_var2 = 200;
#endif
  int b_var3 = 30;
  int b_var4 = 40;
  int b_var5 = 50;
#if V1
  return c(b_var4, b_var5);
#else
  return c(b_var3, b_var4);
#endif
}

int a(int arg1, int arg2) {
  int a_var1 = 1;
  int a_var2;
#if V1
  a_var2 = 21;
#else
  a_var2 = 20;
#endif
  int a_var3 = 3;
  int a_var4 = 4;
  int a_var5 = 5;
  return b(a_var4, a_var5);
}

int main()
{
  std::cout << "Result:" << a(1, 2) << std::endl;
  return 0;
}
