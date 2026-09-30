#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "BrawlerTypes.h"
#include "BrawlerStageData.h"
#include "BrawlerGameMode.generated.h"

class ABrawlerPlayer;
class ABrawlerEnemy;
class ABrawlerFighter;
class ABrawlerCamera;
class ABrawlerStage;
class UAudioComponent;
class UBrawlerMenu;
class UBrawlerSettings;

UENUM(BlueprintType)
enum class EBrawlerFlow : uint8
{
	Title,
	Intro,
	Playing,
	StageClear,
	GameOver,
	Ending
};

/**
 * Steuert den Spielablauf ueber alle Stages (Daten: BrawlerStageData):
 * Titelbild, Kaempfe/Wellen, Kamera, Punkte, Leben, Stage-Wechsel, Game Over, Abspann.
 */
UCLASS()
class STREETSOFBERLIN_API ABrawlerGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ABrawlerGameMode();

	virtual void StartPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer) override;

	// --- Abfragen -----------------------------------------------------------
	ABrawlerPlayer* GetPlayer() const { return Player; }
	float GetCameraX() const { return CameraX; }
	float GetViewMinX() const { return CameraX - Brawler::ScreenWidth * 0.5f; }
	float GetViewMaxX() const { return CameraX + Brawler::ScreenWidth * 0.5f; }
	EBrawlerFlow GetFlow() const { return Flow; }
	int32 GetScore() const { return Score; }
	int32 GetLives() const { return Lives; }
	int32 GetComboHits() const { return ComboHits; }
	float GetComboTimer() const { return ComboTimer; }
	float GetGoArrowTimer() const { return GoArrowTimer; }
	float GetFlowTime() const { return FlowTime; }
	bool IsBossFight() const { return bBossActive; }
	int32 GetStageIndex() const { return StageIndex; }
	int32 GetStageCount() const { return BrawlerData::GetStages().Num(); }
	const FStageDef& GetStageDef() const { return BrawlerData::GetStages()[StageIndex]; }
	ABrawlerFighter* GetLastHitEnemy() const { return LastHitEnemy.Get(); }
	float GetLastHitEnemyTimer() const { return LastHitEnemyTimer; }
	int32 GetAliveEnemyCount() const;

	UBrawlerMenu* GetMenu() const { return Menu; }
	UBrawlerSettings* GetSettings() const { return Settings; }

	// --- Menue-Aktionen -----------------------------------------------------
	/** Figurenauswahl bestaetigt: neues Spiel mit dieser Figur */
	void BeginGame(FName Character);
	void PauseGame();
	void ResumeGame();
	void ReturnToTitle();
	/** Nach Aenderungen im Optionsmenue: Musik an/aus, Lautstaerken */
	void ApplyAudioSettings();

	// --- Ereignisse ---------------------------------------------------------
	void OnStartPressed();
	void OnDamageDealt(ABrawlerFighter* Attacker, ABrawlerFighter* Victim, float Damage);
	void OnEnemyKilled(ABrawlerEnemy* Enemy);
	void OnPlayerDied();
	void AddScore(int32 Amount) { Score += Amount; }

	/** Maximal N Gegner greifen gleichzeitig an (wie in SoR4) */
	bool RequestAttackToken(ABrawlerEnemy* Enemy);
	void ReleaseAttackToken(ABrawlerEnemy* Enemy);

	// --- Effekte ------------------------------------------------------------
	void SpawnEffect(const FString& Prefix, float X, float Depth, float Height, float Facing = 1.f, float FPS = 18.f, float Scale = 1.f);
	void PlaySfx(const FString& Name, float Volume = 1.f, float PitchVariance = 0.08f);
	void ShakeCamera(float Amplitude, float Duration);
	/** Kurzer Zeitlupen-Effekt (Boss-KO) */
	void SlowMotion(float Dilation, float RealSeconds);

	ABrawlerEnemy* SpawnEnemy(FName Type, float X, float Depth);

private:
	void StartMusic();
	float GetMusicVolume() const;
	void StartStage(int32 Index);
	void ClearStageActors();
	void SpawnPlayer(float X, float Depth, bool bDropIn);
	void UpdateCamera(float DeltaSeconds);
	void UpdateEncounters(float DeltaSeconds);
	void SpawnGroup(const FSpawnGroup& Group);
	void SetFlow(EBrawlerFlow NewFlow);

	UPROPERTY()
	TObjectPtr<ABrawlerPlayer> Player;

	UPROPERTY()
	TObjectPtr<ABrawlerCamera> Camera;

	UPROPERTY()
	TObjectPtr<ABrawlerStage> Stage;

	UPROPERTY()
	TObjectPtr<UAudioComponent> Music;

	UPROPERTY()
	TObjectPtr<UBrawlerSettings> Settings;

	UPROPERTY()
	TObjectPtr<UBrawlerMenu> Menu;

	UPROPERTY()
	TArray<TObjectPtr<ABrawlerEnemy>> Enemies;

	TArray<TWeakObjectPtr<ABrawlerEnemy>> AttackTokens;
	TWeakObjectPtr<ABrawlerFighter> LastHitEnemy;
	float LastHitEnemyTimer = 0.f;

	int32 StageIndex = 0;
	int32 NextEncounter = 0;
	int32 ActiveEncounter = INDEX_NONE;
	int32 NextGroup = 0;
	float GroupTimer = 0.f;
	bool bBossActive = false;

	EBrawlerFlow Flow = EBrawlerFlow::Title;
	float FlowTime = 0.f;

	float CameraX = Brawler::ScreenWidth * 0.5f;
	float CameraLockX = -1.f;
	float ShakeTime = 0.f;
	float ShakeAmp = 0.f;
	float SlowMoTimer = 0.f;

	int32 Score = 0;
	int32 Lives = 3;
	int32 ComboHits = 0;
	float ComboTimer = 0.f;
	float GoArrowTimer = 0.f;
	float RespawnTimer = -1.f;
};
