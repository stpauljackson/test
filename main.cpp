#include <iostream>
#include <chrono>
#include <thread>
#include <vector>

using namespace std;

const int M = 1000;
const int N = 1000;
const int K = 9999;

void naive_matmul(float (*A)[K],float (*B)[K],float (*C)[N])
{
    for(int i=0; i<M; i++)
    {
        for(int j=0; j<N; j++)
        {
            
            float temp = 0;
            for(int k=0; k<K; k++)
            {
                temp += A[i][k] * B[j][k];
            }
            C[i][j] = temp;
        }
    }
    return;
}

void matmul_l1_tile(float (*A)[K],float (*B)[K],float (*C)[N])
{

    int tile_size = 48;

    for(int ti=0; ti<M; ti += tile_size)
    {
        for(int tj=0; tj<N; tj += tile_size)
        {
            for(int tk=0; tk<K; tk += tile_size)
            {
                // work on tiles
                int i_max = min(ti + tile_size, M);
                int j_max = min(tj + tile_size, N);
                int k_max = min(tk + tile_size, K);
                for(int i=ti;i<i_max;i++)
                {
                    for(int k=tk;k<k_max;k++)
                    {
                        float temp = A[i][k];
                        for(int j=tj;j<j_max; j++)
                        {
                            C[i][j] += temp * B[j][k];
                        }
                    }
                }
            }
        }
    }
}

int main(int argc, char** argv)
{
    string mode = "naive";
    int nthreads = 4;

    // if(argc > 1) mode = argv[1];
    // if(argc > 2) nthreads = stoi(argv[2]);
    // if(nthreads <= 0) nthreads = 1;

    float (*A)[K] = new float[M][K];

    float (*B)[K] = new float[N][K]; 

    float (*C)[N] = new float[M][N];

    for(int i=0; i<M; i++)
    {
        for(int j=0; j<N; j++)
        {
            C[i][j] = 0;
        }
    }

    vector<thread> T(nthreads);

    auto start = chrono::high_resolution_clock::now();
        
    matmul_l1_tile(A,B,C);

    auto end = chrono::high_resolution_clock::now();

    auto us = chrono::duration_cast<chrono::microseconds>(end - start).count();

    // convert to seconds for GFLOPS
    double time_seconds = us / 1e6;

    // FLOPs
    double total_flops = 2.0 * M * N * K;

    // GFLOPS
    double gflops = total_flops / time_seconds / 1e9;

    cout << "Time: " << us << " us\n";
    cout << "GFLOPS: " << gflops << endl;
    return 0;
}