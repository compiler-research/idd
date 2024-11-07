// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

static char array[1000][1000];

int main (void)
{
  int i, j;

  for (i = 0; i < 1000; i++)
    for (j = 0; j < 1000; j++)
#if V1
        array[i][j]++;
#else
        array[j][i]++;
#endif
  return 0;
}