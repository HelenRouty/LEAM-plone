#define MAIN

#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <grass/gis.h>
#include <grass/site.h>
#include <grass/segment.h>
#include "cost.h"
#include "stash.h"
#include "local_proto.h"
#include <grass/glocale.h>

//FUNCTIONS =====================
void initArrays();
void readInput(double **in, double **xover, double **out);	
void readCostLayer(double **in);
//void readVectorLayer(double **out);
void readStartLayer(double **out);
void readm2(double **in);
void readxover(double **xover, double** out);
int openLayer(char *layerName);
void costAccumulate(double **in, double **xover, double **out);
void writeRaster(double **out);
void cleanup(double **in, double **xover, double **out);

//DECLARE =======================
struct Cell_head window;
extern struct Cell_head window;
struct GModule *module;
struct Flag *flag4;
struct Option *opt1, *opt2, *opt5, *opt7, *opt9;
struct Option *opt10, *opt11, *opt12;

int row;					//Curr Row
int col;					//Curr Column
int nrows;					//Total Rows
int ncols;					//Total Columns
RASTER_MAP_TYPE data_type;	//Input Raster Data Type (int, float, double)		
double **in;				//Cost Layer Raster Values
double **xover;				//Crossover Raster Values
double **out;				//Output Raster Values

//MAIN START ====================
int main(int argc, char *argv[]){

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("raster, cost surface, cumulative costs");
	module->description =
		_("Creates a raster map showing the "
				"cumulative cost of moving between different "
				"geographic locations on an input raster map "
				"whose cell category values represent cost.");

	opt1 = G_define_standard_option(G_OPT_R_OUTPUT);

	opt2 = G_define_standard_option(G_OPT_R_INPUT);
	opt2->description =
		_("Name of input raster map layer whose category values represent surface cost.");

	opt5 = G_define_option();
	opt5->key = "max_cost";
	opt5->type = TYPE_INTEGER;
	opt5->key_desc = "cost";
	opt5->required = NO;
	opt5->multiple = NO;
	opt5->answer = "0";
	opt5->description = _("Optional maximum cumulative cost");

/* Possibly Add vector input later */
/* 
	opt7 = G_define_standard_option(G_OPT_V_INPUT);
    opt7->key = "start_points";
    opt7->required = NO;
    opt7->description = _("Name of starting vector points map");
    opt7->guisection = _("Start");
*/

	opt9 = G_define_standard_option(G_OPT_R_INPUT);
	opt9->key = "start_rast";
	opt9->required = YES;
	opt9->description = _("Name of a raster file that holds the coordinates of starting points from which the transportation cost should be figured.");
	opt9->guisection = _("Start");

	opt10 = G_define_standard_option(G_OPT_V_INPUT);
    opt10->key = "m2";
    opt10->required = YES;
    opt10->description = _("Name of second input raster map containing cost information (required with crossover option).");

	opt11 = G_define_standard_option(G_OPT_V_INPUT);
    opt11->key = "xover";
    opt11->required = YES;
    opt11->description = _("Name of optional raster map containing crossover cells (crossover option).");

	flag4 = G_define_flag();
	flag4->key = 'r';
	flag4->description = _("Start with values in raster map");
	flag4->guisection = _("Start");

	
	/* Parse command line */
	if (G_parser(argc, argv))
		exit(EXIT_FAILURE);

	/*  Get database window parameters      */
	if (G_get_window(&window) < 0){
		G_fatal_error(_("Unable to read current window parameters"));
	}

	nrows = G_window_rows();
	ncols = G_window_cols();

	/*  Check if specified output layer name is legal   */		
	strcpy(cum_cost_layer, opt1->answer);
	if (G_legal_filename(cum_cost_layer) < 0){
		G_fatal_error(_("<%s> is an illegal file name"), cum_cost_layer);
	}


	//Where the work gets done
	initArrays();
	readInput(&*in, &*xover, &*out);
	costAccumulate(&*in, &*xover, &*out);

/*
	for(row = 0; row < nrows; row++){
		for(col = 0; col < ncols; col++){
			if (!G_is_null_value(&out[row][col], data_type)){
				printf("omg its not null val = %f\n", out[row][col]);
			}
		}
	}
*/


//	writeRaster(&*in);
	writeRaster(&*out);

	

	
	//Output bottom half of out
//	sprintf (cum_cost_layer, "%s_2", opt1->answer);
//	writeRaster(&out[nrows]);

	cleanup(&*in, &*xover, &*out);
	
	exit(EXIT_SUCCESS);
}


/*
 * Allocate space for in and out
 */

void initArrays() {
	//double null_cost;
	//G_set_d_null_value(&null_cost, 1);
	
	in = G_malloc(2 * nrows * sizeof(double *));
	xover = G_malloc(nrows * sizeof(double *));	
	out = G_malloc(2 * nrows * sizeof(double *));
	
	for	(row = 0; row < nrows; row++) {	
		in[row] =  G_malloc(ncols * sizeof(double));
		in[row+nrows] =  G_malloc(ncols * sizeof(double));
		xover[row] = G_malloc(ncols * sizeof(double));	
		out[row] =  G_malloc(ncols * sizeof(double));
		out[row+nrows] =  G_malloc(ncols * sizeof(double));
		G_set_d_null_value(out[row], ncols);
		G_set_d_null_value(out[row+nrows], ncols);
		//memmove(out[row], &null_cost, ncols);	
		//memmove(out[row+nrows], &null_cost, ncols);
	}
}


/*
 * Reads the input layers specified by user
 */
void readInput(double **in, double **xover, double **out){	
	// Check for exactly one start point param
	int count = 0;
//	if (opt7->answers)
//	   	count++;
	if (opt9->answers)
	   	count++;

	if (count != 1){
	   	G_fatal_error(_("Must specify exactly one of start_points, start_rast or coordinate"));
	}

	//Read Cost Layer and one set of Start Points
	readxover(&*xover, &*out);				// xover
	readCostLayer(&*in);			// Cost Layer
	readm2(&*in);					// m2

//	if (opt7->answer) {				// Vector Start Points
//		readVectorLayer(&*out);
//	}
//	else
	if (opt9->answer) {		// Raster Start Points
		readStartLayer(&*out); 
	}
	else{
 		G_fatal_error(_("Must specify exactly one of start_points, start_rast or coordinate"));
	}
	
}


/* 
 * Scan the start_points (Vector) layer 
 * searching for starting points.
 */
/*void readVectorLayer(double **out){
	struct Map_info *fp;
	Site *site = NULL;	// pointer to Site
	int got_one = 0;
	int dims, strs, dbls;
	RASTER_MAP_TYPE cat;

	char *search_mapset = G_find_vector(opt7->answer, "");
	if (search_mapset == NULL)
		G_fatal_error(_("Vector map <%s> not found"), opt7->answer);
	
	fp = G_fopen_sites_old(opt7->answer, search_mapset);

	if (G_site_describe(fp, &dims, &cat, &strs, &dbls))
		G_fatal_error(_("Failed to guess site file format"));
		
	site = G_site_new_struct(cat, dims, strs, dbls);

	// Get start points (out and btree initialization)
	while(G_site_get(fp, site) != EOF) {
		if (!G_site_in_region(site, &window))
			continue;

		got_one = 1;

		col = (int)G_easting_to_col(site->east, &window);
		row = (int)G_northing_to_row(site->north, &window);
		
		insert(0, row, col);	//Insert to priority queue
		out[row][col] = 0;		//Set start point value
		
	}

	G_site_free_struct(site);
	G_sites_close(fp);

	if (!got_one)
		G_fatal_error(_("No start points"));

}
*/

void readCostLayer(double **in){
	//DECLARE
	int cost_fd;				//Cost Layer File Descriptor
	int dsize;					//Raster Data Type Size
	void *cell;					//Raster Row Buffer

	//INITIALIZE
	strcpy(cost_layer, opt2->answer);

	cost_fd = openLayer(cost_layer);
	data_type = G_get_raster_map_type(cost_fd);
	dsize = G_raster_size(data_type);
	cell = G_allocate_raster_buf(data_type);
	
	void *ptr;					//pointer for raster column increment
	G_message(_("Reading raster map <%s>..."), cost_layer);
	for (row = 0; row < nrows; row++){
		G_percent(row, nrows, 2);	
		if (G_get_raster_row(cost_fd, cell, row, data_type) < 0){
			G_fatal_error(_("Unable to read raster map <%s> row %d"), cost_layer, row);
		}
		
		ptr = cell;
		for (col = 0; col < ncols; col++){
			in[row][col] = G_get_raster_value_d(ptr, data_type);
			//printf("row: %d col: %d value: %f \n", row, col, in[row][col]);
			ptr = G_incr_void_ptr(ptr, dsize);	//advance cell pointer
		}
	}
	G_percent(1, 1, 1);
	
	//cleanup
	G_close_cell(cost_fd);
	G_free(cell);

}

void readm2(double **in){
	//DECLARE
	int cost_fd;				//Cost Layer File Descriptor
	int dsize;					//Raster Data Type Size
	void *cell;					//Raster Row Buffer
	RASTER_MAP_TYPE data_type;	//Input Raster Data Type (int, float, double)		
	
	//INITIALIZE
	strcpy(cost_layer, opt10->answer);

	cost_fd = openLayer(cost_layer);
	data_type = G_get_raster_map_type(cost_fd);
	dsize = G_raster_size(data_type);
	cell = G_allocate_raster_buf(data_type);
	
	void *ptr;					//pointer for raster column increment
	G_message(_("Reading layer m2 <%s>..."), cost_layer);
	for (row = 0; row < nrows; row++){
		G_percent(row, nrows, 2);	
		if (G_get_raster_row(cost_fd, cell, row, data_type) < 0){
			G_fatal_error(_("Unable to read raster map <%s> row %d"), cost_layer, row);
		}
		
		ptr = cell;
		for (col = 0; col < ncols; col++){
			in[row+nrows][col] = G_get_raster_value_d(ptr, data_type);
			//printf("row: %d col: %d value: %f \n", row, col, in[row][col]);
			ptr = G_incr_void_ptr(ptr, dsize);	//advance cell pointer
		}
	}
	G_percent(1, 1, 1);
	
	//cleanup
	G_close_cell(cost_fd);
	G_free(cell);

}

void readxover(double **xover, double** out){
	//DECLARE
	int cost_fd;				//Cost Layer File Descriptor
	int dsize;					//Raster Data Type Size
	void *cell;					//Raster Row Buffer
	RASTER_MAP_TYPE data_type;	//Input Raster Data Type (int, float, double)		
	
	//INITIALIZE
	strcpy(cost_layer, opt11->answer);

	cost_fd = openLayer(cost_layer);
	data_type = G_get_raster_map_type(cost_fd);
	dsize = G_raster_size(data_type);
	cell = G_allocate_raster_buf(data_type);
	
	void *ptr;					//pointer for raster column increment
	G_message(_("Reading xover layer <%s>..."), cost_layer);
	for (row = 0; row < nrows; row++){
		G_percent(row, nrows, 2);	
		if (G_get_raster_row(cost_fd, cell, row, data_type) < 0){
			G_fatal_error(_("Unable to read raster map <%s> row %d"), cost_layer, row);
		}
		
		ptr = cell;
		for (col = 0; col < ncols; col++){
			xover[row][col] = G_get_raster_value_d(ptr, data_type);
	 //bridges insert(xover[row][col] , row, col, 0);
			//printf("row: %d col: %d value: %f \n", row, col, in[row][col]);
			ptr = G_incr_void_ptr(ptr, dsize);	//advance cell pointer
		}
	}
	G_percent(1, 1, 1);
	
	//cleanup
	G_close_cell(cost_fd);
	G_free(cell);

}


void readStartLayer(double **out){
	
	//DECLARE
	char *start_layer;
	int start_fd;					//Start Layer File Descriptor
	RASTER_MAP_TYPE SL_data_type;	//Start Layer data_type
	int dsize;						//Raster Data Type Size
	void *cell;						//Raster Row Buffer
	double value;					//Raster Cell Value
	int start_with_raster_vals;		//Flag to use start raster vals
	int got_one = 0;				//Need at least one start point
	

	//INITIALIZE
	start_layer = opt9->answer;		//Starting points layer raster name
	start_fd = openLayer(start_layer);
	SL_data_type = G_get_raster_map_type(start_fd);	
	dsize = G_raster_size(SL_data_type);
	cell = G_allocate_raster_buf(SL_data_type);
	start_with_raster_vals = flag4->answer;
	
	void *ptr;					//pointer for column increment
	G_message(_("Reading raster map <%s>..."), start_layer);
	for (row = 0; row < nrows; row++) {
		G_percent(row, nrows, 2);
		if (G_get_raster_row(start_fd, cell, row, SL_data_type) < 0){
			G_fatal_error(_("Unable to read raster map <%s> row %d"), start_layer, row);
		}

		ptr = cell;
		for (col = 0; col < ncols; col++) {	
			if (G_is_null_value(ptr, SL_data_type) /*&& G_is_null_value(&out[row][col], data_type)*/ ){
				out[row][col] = G_get_raster_value_d(ptr, SL_data_type);
			}
			else if(start_with_raster_vals == 1){
				value = G_get_raster_value_d(ptr, SL_data_type);
				insert(value, row, col, 0);	//Insert to priority queue
				out[row][col] = value;
				got_one = 1;
			}
			else {
				value = 0.0;
				insert(value, row, col, 0);	//Insert to priority queue
				out[row][col] = value;
				got_one = 1;
			}

			ptr = G_incr_void_ptr(ptr, dsize);
		}
	}
	G_percent(1, 1, 2);

	G_close_cell(start_fd);
	G_free(cell);

	if (!got_one)
		G_fatal_error(_("No start points"));

}


/*
 * Open cost cell layer for reading.
 * Returns a file descriptor.
 */
int openLayer(char *layer){
    int fd;
	char *mapset;		//Mapset Name Where Raster Map Lives
	
	mapset = G_find_file("cell", layer, "");	
	if (mapset == NULL){
		G_fatal_error(_("Raster map <%s> not found"), layer);
	}
	
    fd = G_open_cell_old(layer, mapset);
    if (fd < 0){
        G_fatal_error(_("Unable to open raster map <%s>"), layer);
    }
	
    return fd;
}



/*---------------------------Benjamin's Main Algorithm------------------------------*/
void costAccumulate(double **in, double **xover, double **out){	
	G_message(_("Finding cost path..."));
	double my_cost;
	double fcost;
	int maxcost;
	double *value;
	double cost;
	double min_cost, old_min_cost;
	struct cost *pres_cell, *new_cell;
	int neighbor;
	

	int n_processed = 0;
	int total_cells = nrows * ncols;
	double NS_fac, EW_fac, DIAG_fac, H_DIAG_fac, V_DIAG_fac;
	
	if (sscanf(opt5->answer, "%d", &maxcost) != 1 || maxcost < 0)
		G_fatal_error(_("Inappropriate maximum cost: %d"), maxcost);
	/*  Find north-south, east_west and diagonal factors */
	EW_fac = 1.0;
	NS_fac = window.ns_res / window.ew_res;
	DIAG_fac = (double)sqrt((double)(NS_fac * NS_fac + EW_fac * EW_fac));
	V_DIAG_fac =
		(double)sqrt((double)(4 * NS_fac * NS_fac + EW_fac * EW_fac));
	H_DIAG_fac =
		(double)sqrt((double)(NS_fac * NS_fac + 4 * EW_fac * EW_fac));
		
	pres_cell = get_lowest();
	int cur_layer;
    while (pres_cell != NULL){		//loop until the tree is empty	
	
        struct cost *ct;
        double N, NE, E, SE, S, SW, W, NW;

        int pres_row = pres_cell->row < nrows ? pres_cell->row : pres_cell->row - nrows;
		double X;
		int do_xover = 0;
		int layernum = 0;
		int layercnt = 1;
		int pres_cell_layer;
		int insert_layer;

		if(xover[pres_row][pres_cell->col] == 1)
		{
			do_xover = 1;
			layercnt = 2;
		}

//printf("xover : %f\n", xover[pres_row][pres_cell->col] );
/*		if(xover[pres_row][pres_cell->col] == 1)
		{
//printf("srow : %d scol : %d \n", pres_cell->row, pres_cell->col);
			if(pres_cell->row < nrows)
			{
	            value = &S;
                S = in[pres_cell->row + nrows][pres_cell->col];   //segment_get(&in_seg, value, row, col);
                fcost = (double)(S + my_cost)/2.0;
                min_cost = pres_cell->min_cost + fcost;
                old_min_cost = out[pres_cell->row+nrows][pres_cell->col];
                if (G_is_d_null_value(&old_min_cost))
                {  //isnan(old_min_cost))
                    out[pres_cell->row+nrows][pres_cell->col] =  min_cost;
                    new_cell = insert(min_cost, pres_cell->row+nrows, pres_cell->col);
                   // printf("row : %d col : %d \n", pres_cell->row+nrows, pres_cell->col);
                }

                else
                {
                    if (old_min_cost > min_cost)
                    {
                        out[pres_cell->row + nrows][pres_cell->col] = min_cost;
                        new_cell = insert(min_cost, pres_cell->row+nrows, pres_cell->col);
                     //   printf("row : %d col : %d \n", pres_cell->row+nrows, pres_cell->col);
                    }
                }


			}
			else
            {
                value = &S;
                S = in[pres_cell->row - nrows][pres_cell->col];   //segment_get(&in_seg, value, row, col);
                fcost = (double)(S + my_cost)/2.0;
                min_cost = pres_cell->min_cost + fcost;
                old_min_cost = out[pres_cell->row-nrows][pres_cell->col];
                if (G_is_d_null_value(&old_min_cost))
                {  //isnan(old_min_cost))
                    out[pres_cell->row-nrows][pres_cell->col] =  min_cost;
                    new_cell = insert(min_cost, pres_cell->row-nrows, pres_cell->col);
                    //printf("row : %d col : %d \n", pres_cell->row-nrows, pres_cell->col);
                }

                else
                {
                    if (old_min_cost > min_cost)
                    {
                        out[pres_cell->row - nrows][pres_cell->col] = min_cost;
                        new_cell = insert(min_cost, pres_cell->row-nrows, pres_cell->col);
                      //  printf("row : %d col : %d \n", pres_cell->row-nrows, pres_cell->col);
                    }
                }


	
            }
       	    

		}
*/








		if (maxcost && ((double)maxcost < pres_cell->min_cost)){
			break;
		}


		old_min_cost = out[pres_cell->row][pres_cell->col];
		if (!G_is_d_null_value(&old_min_cost)){		//isnan(old_min_cost))
			if (pres_cell->min_cost > old_min_cost){
				delete(pres_cell);
				pres_cell = get_lowest();
				continue;
			}
		}

		G_percent(++n_processed, total_cells, 1);
	
    my_cost = in[pres_cell->row][pres_cell->col];


for (layernum = 0; layernum < layercnt; layernum++){
//could add in the layer switching stuff
          if (do_xover){
              if (layernum == 1){
				pres_cell->row = pres_cell->row < nrows ? pres_cell->row + nrows: pres_cell->row-nrows;
              }
          }




	for (neighbor = 1; neighbor <= 8; neighbor++){
		switch (neighbor){		//for each neighbor set the coordinated
			case 1:
				row = pres_cell->row;
				col = pres_cell->col - 1;
				break;
			case 2:
				col = pres_cell->col + 1;
				break;
			case 3:
				row = pres_cell->row - 1;
				col = pres_cell->col;
				break;
			case 4:
				row = pres_cell->row + 1;
				break;
			case 5:
				row = pres_cell->row - 1;
				col = pres_cell->col - 1;
				break;
			case 6:
				col = pres_cell->col + 1;
				break;
			case 7:
				row = pres_cell->row + 1;
				break;
			case 8:
				col = pres_cell->col - 1;
				break;
		}

		if (row < 0 || row >= nrows || (pres_cell->row < nrows && row >= nrows) || (pres_cell->row >= nrows && row < nrows) ){	//if the neighbor is out of bounds, continue
			continue;
		}
		if (col < 0 || col >= ncols ){
			continue;
		}

		value = &cost;
		switch (neighbor){
			case 1:
				value = &W;
				W = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(W + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * EW_fac;
				break;
			case 2:
				value = &E;
				E = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(E + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * EW_fac;
				break;
			case 3:
				value = &N;
				N = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(N + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * NS_fac;
				break;
			case 4:
				value = &S;
				S = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(S + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * NS_fac;
				break;
			case 5:
				value = &NW;
				NW = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(NW + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * DIAG_fac;
				break;
			case 6:
				value = &NE;
				NE = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(NE + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * DIAG_fac;
				break;
			case 7:
				value = &SE;
				SE = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(SE + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * DIAG_fac;
				break;
			case 8:
				value = &SW;
				SW = in[row][col];	//segment_get(&in_seg, value, row, col);
				fcost = (double)(SW + my_cost)/2.0;
				min_cost = pres_cell->min_cost + fcost * DIAG_fac;
				break;
		}
//printf("row : %d col : %d \n", row, col);
/*bridges
		if(xover[pres_row][pres_cell->col] == 1)
		{
			out[row ][col] =  my_cost/2.0+fcost*DIAG_fac;
	        new_cell = insert(min_cost, row, col, cur_layer);
		}
*/
		if (G_is_d_null_value(&min_cost)){	//isnan(min_cost)) //if the min cost is null, next
			continue;
		}

		old_min_cost = out[row][col];

		if (G_is_d_null_value(&old_min_cost)){	//isnan(old_min_cost))
			out[row ][col] =  min_cost;
			new_cell = insert(min_cost, row, col, cur_layer);
			//printf("row : %d col : %d \n", row, col);
		}
		else {
			if (old_min_cost > min_cost){
				out[row][col] = min_cost;

				new_cell = insert(min_cost, row, col, cur_layer);
			//printf("row : %d col : %d \n", row, col);
			}
		}

	}
}





        ct = pres_cell;
        delete(pres_cell);

        pres_cell = get_lowest();
        if (pres_cell == NULL) {
            G_message(_("No data"));
            //return 4;
            break;
        }

        if (ct == pres_cell)
            G_warning(_("Error, ct == pres_cell"));

//printf("erow : %d ecol : %d \n", pres_cell->row, pres_cell->col);
//printf("hahah\n"); return 4;
    }

	G_percent(1, 1, 1);
	
	return;

}


void writeRaster(double **out){
	G_message(_("Writing raster map <%s>..."), cum_cost_layer);
	
	double peak = 0.0;
	double min_cost = 0.0;
	int cum_fd = G_open_raster_new(cum_cost_layer, data_type);
	
	for (row = 0; row < nrows; row++){
		G_percent(row, nrows, 2);
		for (col = 0; col < ncols; col++){
			min_cost = out[row][col];
		    if (min_cost > peak)
				peak = min_cost;
		}
		G_put_raster_row(cum_fd, out[row], data_type);
	}
	G_percent(1, 1, 1);

	G_close_cell(cum_fd);
    
	G_done_msg(_("Peak cost value: %f."), peak);

	return;
}


void cleanup(double **in, double **xover, double **out){
	for(row = 0; row < nrows; row++){
		G_free(in[row]);
		G_free(xover[row]);
		G_free(out[row]);
	}

	G_free(in);
	G_free(xover);
	G_free(out);

	return;
}


