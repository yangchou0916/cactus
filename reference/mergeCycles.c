#include "sonLib.h"
#include "cactus.h"
#include "adjacencyPairs.h"
#include "adjacencyPairsHash.h"
#include "adjacencyPairComponents.h"
#include "adjacencySwitch.h"

static void splitIntoContigsAndCycles(stList *components, stList **contigs,
        stList **cycles) {
    /*
     * Divides the list of components into rings and components terminated by a pair of stubs.
     */
    End *end1, *end2;
    *cycles = stList_construct();
    *contigs = stList_construct();
    stList *component;
    for (int32_t i = 0; i < stList_length(components); i++) {
        component = stList_get(components, i);
        getAttachedStubEndsInComponent(component, &end1, &end2);
        if (end1 != NULL) {
            assert(end2 != NULL);
            stList_append(*contigs, component);
        } else {
            assert(end2 == NULL);
            stList_append(*cycles, component);
        }
    }
}

void mergeCycles(stHash *adjacencies, Flower *flower) {
    stList *contigs, *cycles;

    //Get the comopnents to merge.
    stList *components = adjacencyHash_getConnectedComponents(adjacencies,
            flower);

    //Get the cycles and contigs
    splitIntoContigsAndCycles(components, &contigs, &cycles);

    //Iterate on the cycles merging them until we have none.
    while (stList_length(cycles) > 0) { //Now merge the cycles
        AdjacencySwitch *adjacencySwitch = NULL;
        stList *mergingComponent = NULL;
        stList *cycle = stList_pop(cycles);
        for (int32_t j = 0; j < stList_length(components); j++) {
            stList *component = stList_get(components, j);
            if (cycle != component) {
                stList *adjacencySwitches =
                        adjacencySwitch_getAdjacencySwitches(cycle, component);
                if (stList_length(adjacencySwitches) > 0) {
                    stList_sort(adjacencySwitches, (int (*)(const void *, const void *))adjacencySwitch_cmpByStrength);
                    AdjacencySwitch *adjacencySwitch2 = stList_pop(adjacencySwitches);
                    if (adjacencySwitch == NULL
                            || adjacencySwitch_cmpByStrength(adjacencySwitch2,
                                    adjacencySwitch) >= 0) {
                        if (adjacencySwitch != NULL) {
                            adjacencySwitch_destruct(adjacencySwitch);
                        }
                        adjacencySwitch = adjacencySwitch2;
                        mergingComponent = component;
                    }
                }
                stList_destruct(adjacencySwitches);
            }
        }
        assert(adjacencySwitch != NULL);

        //Do the switch
        adjacencySwitch_switch(adjacencySwitch, adjacencies);

        //Component the new component..
        stList *newComponent = adjacencyHash_getConnectedComponent(adjacencies,
                flower, adjacencyPair_getEnd1(
                        adjacencySwitch_getAdjacencyPair1(adjacencySwitch)));
        assert(stList_length(cycle) + stList_length(mergingComponent) == stList_length(newComponent));

        //Update the list of components
        stList_removeItem(components, cycle);
        stList_removeItem(components, mergingComponent);
        stList_append(components, newComponent);
        //Update the list of cycles.
        if (stList_contains(cycles, mergingComponent)) {
            stList_removeItem(cycles, mergingComponent);
            stList_append(cycles, newComponent);
        }
        //Destroy the old components.
        stList_destruct(cycle);
        stList_destruct(mergingComponent);

        //Destroy the switch and adjacency pairs
        adjacencyPair_destruct(adjacencySwitch_getAdjacencyPair1(
                adjacencySwitch));
        adjacencyPair_destruct(adjacencySwitch_getAdjacencyPair2(
                adjacencySwitch));
        adjacencySwitch_destruct(adjacencySwitch);

    }
    stList_destruct(contigs);
    stList_destruct(cycles);
    stList_destruct(components);

#ifdef BEN_DEBUG
    components = adjacencyHash_getConnectedComponents(adjacencies, flower);
    splitIntoContigsAndCycles(components, &contigs, &cycles);
    assert(stList_length(cycles) == 0);
    assert(stList_length(contigs) > 0);
    assert(stList_length(contigs) == stList_length(components));
    stList_destruct(contigs);
    stList_destruct(cycles);
    stList_destruct(components);
#endif
}
