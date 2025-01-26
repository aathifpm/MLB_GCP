import pandas as pd
from typing import List, Dict
import requests
from requests.exceptions import RequestException

class HomeRunsFetcher:
    """Handles fetching and processing MLB home runs data from provided CSV files."""
    
    def __init__(self):
        """Initialize the home runs data fetcher."""
        self.mlb_hr_csvs_list = [
            'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2016-mlb-homeruns.csv',
            'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2017-mlb-homeruns.csv',
            'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2024-mlb-homeruns.csv',
            'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2024-postseason-mlb-homeruns.csv'
        ]
    
    def fetch_all_home_runs(self) -> pd.DataFrame:
        """
        Fetch and process all MLB home runs data from the provided CSV files.
        
        Returns:
            DataFrame containing processed home runs data from all seasons
        """
        dfs = []
        
        for csv_url in self.mlb_hr_csvs_list:
            try:
                # Extract season from the URL
                season = csv_url.split('/')[-1].split('-')[0]
                
                # Read CSV file
                df = pd.read_csv(csv_url)
                
                # Add season column
                df['season'] = season
                
                dfs.append(df)
                
            except Exception as e:
                print(f"Error processing {csv_url}: {str(e)}")
                continue
        
        if not dfs:
            raise Exception("Failed to load any home runs data")
            
        # Combine all DataFrames
        all_mlb_hrs = pd.concat(dfs, ignore_index=True)
        
        # Select and reorder columns
        columns = ['season', 'play_id', 'title', 'ExitVelocity', 'LaunchAngle', 'HitDistance', 'video']
        all_mlb_hrs = all_mlb_hrs[columns]
        
        return all_mlb_hrs
    
    def fetch_home_runs_by_season(self, season: str) -> pd.DataFrame:
        """
        Fetch home runs data for a specific season.
        
        Args:
            season: The season year to fetch data for (e.g., '2024')
            
        Returns:
            DataFrame containing home runs data for the specified season
        """
        csv_url = next((url for url in self.mlb_hr_csvs_list if season in url), None)
        
        if not csv_url:
            raise ValueError(f"No data available for season {season}")
            
        try:
            df = pd.read_csv(csv_url)
            df['season'] = season
            
            # Select and reorder columns
            columns = ['season', 'play_id', 'title', 'ExitVelocity', 'LaunchAngle', 'HitDistance', 'video']
            return df[columns]
            
        except Exception as e:
            raise Exception(f"Error fetching data for season {season}: {str(e)}") 