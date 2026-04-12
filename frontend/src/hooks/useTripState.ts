import { useState, useCallback } from 'react';

interface TripState {
  destination?: string;
  dates?: {
    start: string;
    end: string;
  };
  interests?: string[];
  budget?: string;
  itinerary?: Array<{
    day: number;
    activities: Array<{
      time: string;
      name: string;
      description: string;
      cost?: string;
    }>;
  }>;
  flights?: Array<{
    airline: string;
    departure: string;
    arrival: string;
    price: string;
  }>;
}

export function useTripState() {
  const [tripState, setTripState] = useState<TripState | null>(null);

  const updateTripState = useCallback((newState: Partial<TripState>) => {
    setTripState((prev) => ({
      ...prev,
      ...newState,
    }));
  }, []);

  return { tripState, updateTripState };
}

