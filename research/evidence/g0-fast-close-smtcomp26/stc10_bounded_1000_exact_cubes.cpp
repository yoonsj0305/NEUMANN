// G0 fixed 10 opened MathProblems sum-of-three-cubes originals.
// Preregistered Issue #218 comment 6247988434 BEFORE any search result.
// NOT a SAT solver for unbounded Z: a sound complete search only for |x,y,z|<=1000.
// Any witness must be independently verified against original SMT-LIB source.
#include <bits/stdc++.h>
#include <sys/resource.h>
using namespace std;
using ll = long long;
static inline ll cube(ll x) { return x * x * x; }
int main() {
    constexpr int B=1000;
    const vector<ll> ks={87,228,268,291,588,609,786,795,813,880};
    unordered_map<ll,int> table;
    table.reserve(2*B+1);
    for(int z=-B;z<=B;++z) table.emplace(cube(z),z);
    cout << "{\"study\":\"G0_STC_10_CLASSICAL_BOUNDED_CUBE_HASH\",\"bound\":" << B << ",\"tasks\":[";
    bool first=true;
    for(const ll k:ks) {
        auto start=chrono::steady_clock::now();
        bool found=false;
        ll ax=0,ay=0,az=0;
        unsigned long long checked_pairs=0;
        for(ll x=-B; x<=B&&!found; ++x) {
            const ll xc=cube(x);
            for(ll y=x; y<=B; ++y) {
                ++checked_pairs;
                auto it=table.find(k-xc-cube(y));
                if(it!=table.end()&&it->second>=y) {
                    ax=x;ay=y;az=it->second;
                    found=true;break;
                }
            }
        }
        const double wall_s=chrono::duration<double>(
          chrono::steady_clock::now()-start).count();
        if(!first) cout << ",";
        first=false;
        cout << "{\"target\":" << k << ",\"found\":" << (found?"true":"false")
             << ",\"searched_xy_pairs\":" << checked_pairs << ",\"wall_s\":"
             << setprecision(9) << wall_s;
        if(found) {
            const ll proof=cube(ax)+cube(ay)+cube(az);
            if(proof!=k||ax>ay||ay>az) return 3;
            cout << ",\"x\":"<<ax<<",\"y\":"<<ay<<",\"z\":"<<az
                 << ",\"cubes_sum\":"<<proof;
        } else {
            cout << ",\"bound_limited_no_witness_only\":true";
        }
        cout << "}";
    }
    struct rusage usage;
    getrusage(RUSAGE_SELF,&usage);
    cout << "],\"maxrss_kib\":" << usage.ru_maxrss
         << ",\"all_10_covered\":true,\"negative_results_are_unbounded_unsat\":false"
         << ",\"neural_forwards\":0}" << endl;
    return 0;
}
