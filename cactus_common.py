"""Setup functions for assisting in testing the various modules of the cactus package.
"""

import random
import os

from sonLib.bioio import logger
from sonLib.bioio import getTempFile
from sonLib.bioio import getTempDirectory
from sonLib.bioio import getRandomSequence
from sonLib.bioio import mutateSequence
from sonLib.bioio import reverseComplement
from sonLib.bioio import fastaWrite
from sonLib.bioio import printBinaryTree
from sonLib.bioio import system
from sonLib.bioio import getRandomAlphaNumericString

from sonLib.tree import makeRandomBinaryTree

from workflow.jobTree.jobTree import runJobTree
from workflow.jobTree.jobTreeTest import runJobTreeStatusAndFailIfNotComplete

def getRandomCactusInputs(tempDir,
                          sequenceNumber=random.choice(xrange(100)), 
                          avgSequenceLength=random.choice(xrange(1, 5000)), 
                          treeLeafNumber=random.choice(xrange(1, 10))):
    """Gets a random set of sequences, each of length given, and a species
    tree relating them. Each sequence is a assigned an event in this tree.
    """
    
    #Make tree
    binaryTree = makeRandomBinaryTree(treeLeafNumber)
    newickTreeString = printBinaryTree(binaryTree, includeDistances=True)
    newickTreeLeafNames = []
    def fn(tree):
        if tree.internal:
            fn(tree.left)
            fn(tree.right)
        else:
            newickTreeLeafNames.append(tree.iD)
    fn(binaryTree)
    logger.info("Made random binary tree: %s" % newickTreeString)
    
    sequenceDirs = []
    for i in xrange(len(newickTreeLeafNames)):
        seqDir = getTempDirectory(rootDir=tempDir)
        sequenceDirs.append(seqDir)
        
    logger.info("Made a set of random directories: %s" % " ".join(sequenceDirs))
    
    #Random sequences and species labelling
    sequenceFile = None
    fileHandle = None
    parentSequence = getRandomSequence(length=random.choice(xrange(1, 2*avgSequenceLength)))[1]
    for i in xrange(sequenceNumber):
        if sequenceFile == None:
            sequenceFile = getTempFile(rootDir=random.choice(sequenceDirs), suffix=".fa")
            fileHandle = open(sequenceFile, 'w')
        if random.random() > 0.8: #Get a new root sequence
            parentSequence = getRandomSequence(length=random.choice(xrange(1, 2*avgSequenceLength)))[1]
        sequence = mutateSequence(parentSequence, distance=random.random()*0.5)
        name = getRandomAlphaNumericString(15)
        if random.random() > 0.5:
            sequence = reverseComplement(sequence)
        fastaWrite(fileHandle, name, sequence)
        if random.random() > 0.5:
            fileHandle.close()
            fileHandle = None
            sequenceFile = None
    if fileHandle != None:
        fileHandle.close()
        
    logger.info("Made %s sequences in %s directories" % (sequenceNumber, len(sequenceDirs)))
    
    return sequenceDirs, newickTreeString

def runCactusSetup(reconstructionRootDir, sequences, 
                   newickTreeString, tempDir, logLevel="DEBUG", debug=False):
    debugString = ""
    if debug:
        debugString = "--debug"
    system("cactus_setup %s --speciesTree '%s' --netDisk %s \
--logLevel %s %s" \
           % (" ".join(sequences), newickTreeString,
              reconstructionRootDir, logLevel, debugString))
    logger.info("Ran cactus setup okay")
    
def runCactusAligner(netDisk, alignmentFile, tempDir, useDummy=True, netName="0", logLevel="DEBUG"):        
    """Runs job tree and fails if not complete.
    """
    tempDir = getTempDirectory(tempDir)
    jobTreeDir = os.path.join(tempDir, "jobTree")
    if useDummy:
        useDummy = "--useDummy"
    else:
        useDummy = ""
    command = "cactus_aligner.py --netDisk %s --netName %s \
--resultsFile %s %s --job JOB_FILE" % (netDisk, netName, alignmentFile, useDummy)
    runJobTree(command, jobTreeDir, logLevel=logLevel)
    runJobTreeStatusAndFailIfNotComplete(jobTreeDir)
    system("rm -rf %s" % tempDir)
    logger.info("Ran the cactus aligner okay")
            
def runCactusCore(netDisk, alignmentFile, tempDir, 
                  netName=0,
                  logLevel="DEBUG", writeDebugFiles=False,
                  maximumEdgeDegree=None,
                  proportionOfAtomsToKeep=None,
                  discardRatio=None,
                  minimumTreeCoverage=None,
                  minimumChainLength=None):
    if writeDebugFiles:
        writeDebugFiles = "--writeDebugFiles"
    else:
        writeDebugFiles = ""
        
    if maximumEdgeDegree:
        maximumEdgeDegree = "--maxEdgeDegree %i" % maximumEdgeDegree
    else:
        maximumEdgeDegree = ""
        
    if proportionOfAtomsToKeep:
        proportionOfAtomsToKeep = "--proportionToKeep %f" % proportionOfAtomsToKeep
    else:
        proportionOfAtomsToKeep = ""
    
    if discardRatio:
        discardRatio = "--discardRatio %f" % discardRatio
    else:
        discardRatio = ""
        
    if minimumTreeCoverage:
        minimumTreeCoverage = "--minimumTreeCoverage %f" % minimumTreeCoverage
    else:
        minimumTreeCoverage = ""
    
    if minimumChainLength:
        minimumChainLength = "--minimumChainLength %i" % minimumChainLength
    else:
        minimumChainLength = ""
    
    command = "cactus_core --netDisk %s --netName %s --alignments %s \
--tempDirRoot %s --logLevel %s \
%s %s %s %s %s %s" % \
    (netDisk, netName, alignmentFile, 
     tempDir, logLevel, writeDebugFiles,
     maximumEdgeDegree, proportionOfAtomsToKeep, discardRatio, minimumTreeCoverage, minimumChainLength)
    #logger.info("Running command: %s" % command)
    #sys.exit(1)
    system(command)
    logger.info("Ran cactus_core okay")
    
def runCactusPhylogeny(netDisk, tempDir, 
                  netName=0,
                  logLevel="DEBUG"):
    command = "cactus_phylogeny --netDisk %s --netName %s --tempDirRoot %s --logLevel %s " % \
    (netDisk, netName, tempDir, logLevel)
    system(command)
    logger.info("Ran cactus_phylogeny okay")
    
def runCactusAdjacencyBuilder(reconstructionRootDir, reconstructionProblem, tempDir, 
                              uniqueNamePrefix=getRandomAlphaNumericString(),
                              adjacencyProgram="cactus_adjacencyTestAdjacencyBuilder.py", logLevel="DEBUG"):
    
    command = "%s --absolutePathPrefix %s --reconstructionProblem %s --uniqueNamePrefix %s \
--tempDirRoot %s --logLevel %s" % (adjacencyProgram, reconstructionRootDir, reconstructionProblem, uniqueNamePrefix, 
                                   tempDir, logLevel)
    logger.info("Running command : %s" % command)
    system(command)
    logger.info("Adjacency builder ran okay")
    
def runCactusTreeViewer(graphFile,
                        netDisk, 
                        netName="0", 
                        logLevel="DEBUG", nodesProportionalTo="atoms"):
    system("cactus_treeViewer --netDisk %s --netName %s --outputFile %s --logLevel %s" \
                    % (netDisk, netName, graphFile, logLevel))
    logger.info("Created a cactus tree graph")

def runCactusCheck(netDisk, 
                    netName="0", 
                    logLevel="DEBUG"):
    system("cactus_check --netDisk %s --netName %s --logLevel %s" \
                    % (netDisk, netName, logLevel))
    logger.info("Ran cactus check")
    
def runCactusAtomGraphViewer(graphFile,
                             reconstructionRootDir, 
                             reconstructionProblem="reconstructionProblem.xml", 
                             logLevel="DEBUG", includeCaps=False, includeInternalAdjacencies=False):
    if includeCaps:
        includeCaps = "--includeCaps"
    else:
        includeCaps = ""
    if includeInternalAdjacencies:
        includeInternalAdjacencies = "--includeInternalAdjacencies"
    else:
        includeInternalAdjacencies = ""
    system("cactus_atomGraphViewer.py --absolutePathPrefix %s --reconstructionProblem %s --graphFile %s --logLevel %s %s %s" \
                    % (reconstructionRootDir, reconstructionProblem, graphFile, logLevel, includeCaps, includeInternalAdjacencies))
    logger.info("Created a break point graph of the problem")
    
def runCactusWorkflow(netDisk, sequenceFiles, 
                      newickTreeString, 
                      jobTreeDir, treeBuilder="cactus_coreTestTreeBuilder.py",
                      adjacencyBuilder="cactus_adjacencyTestAdjacencyBuilder.py",
                      logLevel="DEBUG", retryCount=0, batchSystem="single_machine", rescueJobFrequency=None, alignmentIterations=None):
    if alignmentIterations != None:
        alignmentIterationsString = "--alignmentIterations=%s" % alignmentIterations
    else:
        alignmentIterationsString = ""
    command = "cactus_workflow.py %s --speciesTree '%s' \
--netDisk %s %s --job JOB_FILE" % \
            (" ".join(sequenceFiles), newickTreeString,
             netDisk, alignmentIterationsString)
    runJobTree(command, jobTreeDir, logLevel, retryCount, batchSystem, rescueJobFrequency)
    logger.info("Ran the cactus workflow for %s okay" % netDisk)

