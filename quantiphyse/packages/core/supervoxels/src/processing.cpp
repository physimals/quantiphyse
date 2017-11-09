
#include "processing.h"

long distance_measure(int ax, int ay, int az, int bx, int by, int bz)
{

    int dx, dy, dz;
    long dmeas;

    dx = (bx - ax);
    dy = (by - ay);
    dz = (bz - az);

    dmeas = dx*dx + dy*dy + dz*dz;

    return dmeas;
}

// Get the vector distance (x, y, z) of the maximum distance between two closest points
vector<int> get_mean_point_distance(vector<int> & x, vector<int> & y, vector<int> & z)
{
    vector<int> dist (3, 0);
    vector<int> sx;
    vector<int> sy;
    vector<int> sz;

    long dmeas = numeric_limits<long>::max();
    long dist1;


    for (int m=0; m<x.size(); m++)
    {
        for (int n=0; n<x.size(); n++)
        {
            // Skip comparing point to itself
            if (n==m)
                continue;

            // Calculate the squared distance between each point and every other
            dist1 = distance_measure(x[m], y[m], z[m], z[n], y[n], z[n]);
            if (dist1 < dmeas)
            {
                // If closer then save the vector distance for that point
                dmeas = dist1;
                sx.push_back(abs(x[m] - x[n]));
                sy.push_back(abs(y[m] - y[n]));
                sz.push_back(abs(z[m] - z[n]));
            }

        }
    }

    // Find the maximum distance between two points in the region and use this for the supervoxel extraction
    dist[0] = *max_element(sx.begin(), sx.end());
    dist[1] = *max_element(sy.begin(), sy.end());
    dist[2] = *max_element(sz.begin(), sz.end());

    return dist;
}