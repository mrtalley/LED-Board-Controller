

// -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; -*-
//
// This code is public domain
// (but note, once linked against the led-matrix library, this is
// covered by the GPL v2)

#include "led-matrix.h"
#include "threaded-canvas-manipulator.h"
#include "transformer.h"
#include "graphics.h"

#include <assert.h>
#include <getopt.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <algorithm>

using std::min;
using std::max;

using namespace rgb_matrix;

/*
 * The following are demo image generators. They all use the utility
 * class ThreadedCanvasManipulator to generate new frames.
 */

// Imitation of volume bars
// Purely random height doesn't look realistic
// Contributed by: Vliedel
class VolumeBars : public ThreadedCanvasManipulator {
public:
  VolumeBars(Canvas *m, int delay_ms=50, int numBars=8)
    : ThreadedCanvasManipulator(m), delay_ms_(delay_ms),
      numBars_(numBars), t_(0) {
  }

  ~VolumeBars() {
    delete [] barHeights_;
    delete [] barFreqs_;
    delete [] barMeans_;
  }

  void Run() {
    const int width = canvas()->width();
    height_ = canvas()->height();
    barWidth_ = width/numBars_;
    barHeights_ = new int[numBars_];
    barMeans_ = new int[numBars_];
    barFreqs_ = new int[numBars_];
    heightGreen_  = height_*4/12;
    heightYellow_ = height_*8/12;
    heightOrange_ = height_*10/12;
    heightRed_    = height_*12/12;

    // Array of possible bar means
    int numMeans = 10;
    int means[10] = {1,2,3,4,5,6,7,8,16,32};
    for (int i=0; i<numMeans; ++i) {
      means[i] = height_ - means[i]*height_/8;
    }
    // Initialize bar means randomly
    srand(time(NULL));
    for (int i=0; i<numBars_; ++i) {
      barMeans_[i] = rand()%numMeans;
      barFreqs_[i] = 1<<(rand()%3);
    }

    // Start the loop
    while (running()) {
      if (t_ % 8 == 0) {
        // Change the means
        for (int i=0; i<numBars_; ++i) {
          barMeans_[i] += rand()%3 - 1;
          if (barMeans_[i] >= numMeans)
            barMeans_[i] = numMeans-1;
          if (barMeans_[i] < 0)
            barMeans_[i] = 0;
        }
      }

      // Update bar heights
      t_++;
      for (int i=0; i<numBars_; ++i) {
        barHeights_[i] = (height_ - means[barMeans_[i]])
          * sin(0.1*t_*barFreqs_[i]) + means[barMeans_[i]];
        if (barHeights_[i] < height_/8)
          barHeights_[i] = rand() % (height_/8) + 1;
      }

      for (int i=0; i<numBars_; ++i) {
        int y;
        for (y=0; y<barHeights_[i]; ++y) {
          if (y<heightGreen_) {
            drawBarRow(i, y, 0, 200, 0);
          }
          else if (y<heightYellow_) {
            drawBarRow(i, y, 150, 150, 0);
          }
          else if (y<heightOrange_) {
            drawBarRow(i, y, 250, 100, 0);
          }
          else {
            drawBarRow(i, y, 200, 0, 0);
          }
        }
        // Anything above the bar should be black
        for (; y<height_; ++y) {
          drawBarRow(i, y, 0, 0, 0);
        }
      }
      usleep(delay_ms_ * 1000);
    }
  }

private:
  void drawBarRow(int bar, uint8_t y, uint8_t r, uint8_t g, uint8_t b) {
    for (uint8_t x=bar*barWidth_; x<(bar+1)*barWidth_; ++x) {
      canvas()->SetPixel(x, height_-1-y, r, g, b);
    }
  }

  int delay_ms_;
  int numBars_;
  int* barHeights_;
  int barWidth_;
  int height_;
  int heightGreen_;
  int heightYellow_;
  int heightOrange_;
  int heightRed_;
  int* barFreqs_;
  int* barMeans_;
  int t_;
};
