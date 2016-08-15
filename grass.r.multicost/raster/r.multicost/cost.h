/***************************************************************/
/*                                                             */
/*        cost.h    in   ~/src/Gcost                           */  
/*                                                             */
/*      This header file defines the data structure of a       */  
/*      point structure containing various attributes of       */
/*      a grid cell.                                           */
/*                                                             */
/***************************************************************/
 /*DKS added layer for xover support: 0 = base layer, 1 = second layer */
struct cost{
    double  min_cost;
    int row;
    int col;
    int layer;
    struct cost *lower;
    struct cost *higher;
    struct cost *above;
    struct cost *nexttie;
    struct cost *previoustie;
};

/* btree.c */
struct cost *insert(double, int, int, int); /*DKS: added int param for layer*/
struct cost *find(double, int, int, int); /*DKS: added int param for layer, altho this function
                                           seems not be used*/
struct cost *get_lowest(void);
int show(struct cost *);
int show_all();
int delete(struct cost *);
int check(char *, struct cost *);
/***************************************************************/
