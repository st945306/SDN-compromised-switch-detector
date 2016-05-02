/*
"""""""""""""
Max port num = 50
argv1 = switch num

portMap[(aid, aport)] = (bid, bport)

portMap[(1,2)] = (2,2)

"""""""""""""
*/

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define MAX_NUM 101
#define MAX_PORT_NUM 250

void init_map(int a[][MAX_NUM]) {
	int i,j;
	for(i=0; i<MAX_NUM; i++)
		for(j=0;j<MAX_NUM;j++)
			a[i][j] = -1;
	return;
}
void init_topo(int switch_num, int connect_map[][MAX_NUM], int port[][MAX_PORT_NUM]) {
	int i;
	for(i = 1; i < switch_num; i++) {
		int portid1, portid2;
		do {
			portid1 = rand() % MAX_PORT_NUM+1;
			portid2 = rand() % MAX_PORT_NUM+1;
		}while(port[i][portid1] || port[i+1][portid2]);
		port[i][portid1] = 1;
		port[i+1][portid2] = 1;
		connect_map[i][i+1] = portid1;
		connect_map[i+1][i] = portid2; 
			
	}
	return;
}
int main(int argc, char **argv) {
	srand(time(NULL));
	int switch_num = atoi(argv[1]);
	printf("%d\n", switch_num);
	int i, j;	
	
	int port[MAX_NUM][MAX_PORT_NUM] = {0};
	int connect_map[MAX_NUM][MAX_NUM];  // connect_map[switch id][switch id] = port num or not connect(-1);
	init_map(connect_map);
	init_topo(switch_num, connect_map, port);
	/*
	for(i = 1; i <= switch_num; i++) {
		for(j = 1; j <= switch_num; j++) {
			printf("%3d ",connect_map[i][j]);
		}
		printf("\n");
	}
	*/
	//printf("===========\n");
	for(i = 1; i < switch_num; i++) {
		for(j = i+1; j <= switch_num; j++) {
			if(connect_map[i][j] == -1) {
				int isConnect = rand() % 2;
				if(isConnect) {
					int portid1, portid2;
					do {
						portid1 = rand() % MAX_PORT_NUM+1;
						portid2 = rand() % MAX_PORT_NUM+1;
					}while(port[i][portid1] || port[j][portid2]);
					port[i][portid1] = 1;
					port[j][portid2] = 1;
					connect_map[i][j] = portid1;
					connect_map[j][i] = portid2; 
				}
			}
		}
	}
	/*
	for(i = 1; i <= switch_num; i++) {
		for(j = 1; j <= switch_num; j++) {
			printf("%3d ",connect_map[i][j]);
		}
		printf("\n");
	}
	*/
	FILE *fp = fopen("randTopo.py", "w");
	fprintf(fp, "switchNum = %d\n", switch_num);
	fprintf(fp, "portMap = {}\n");
	for(i = 1; i <= switch_num; i++) {
		for(j = 1; j <= switch_num; j++) {
			if(connect_map[i][j] != -1)
				fprintf(fp,"portMap[(%d, %d)] = (%d, %d)\n", 
						i, connect_map[i][j], j, connect_map[j][i]);
		}
	}

	fclose(fp);
	return 0;
}
