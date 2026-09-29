#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "BrawlerTypes.h"
#include "BrawlerGameMode.generated.h"

class ABrawlerPlayer;
class ABrawlerEnemy;
class ABrawlerFighter;
class ABrawlerCamera;
class ABrawlerStage;
class UAudioComponent;

UENUM(BlueprintType)
enum class EBrawlerFlow : uint8
{
	Title,
	Intro,
	Playing,
	StageClear,
	GameOver
};

/** Eine Gegnergruppe innerhalb eines Kampfes */
struct FSpawnGroup
{
	TArray<FName> Enemies;
	/** Gruppe erscheint, sobald hoechstens so viele Gegner leben ... */
	int32 WhenAliveAtMost = 0;
	/** ... oder spaetestens nach dieser Zeit seit dem letzten Spawn */
	float MaxDelay = 12.f;
};

/** Ein Kampf-Abschnitt: Kamera wird gesperrt, bis alle Gruppen besiegt sind */
struct FEncounter
{
	float TriggerX = 0.f;
	float LockCenterX = 0.f;
	TArray<FSpawnGroup> Groups;
	bool bBoss = false;
};

struct FPropSpawn
{
	FName Type;
	float X = 0.f;
	float Depth = 0.f;
	FName Drop;
};

/**
 * Steuert den Ablauf von Stage 1 "Kreuzberg bei Nacht":
 * Titelbild, Kaempfe/Wellen, Kamera, Punkte, Leben, Game Over.
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
	ABrawlerFighter* GetLastHitEnemy() const { return LastHitEnemy.Get(); }
	float GetLastHitEnemyTimer() const { return LastHitEnemyTimer; }
	int32 GetAliveEnemyCount() const;

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
	void BuildStageData();
	void StartGame();
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
	TArray<TObjectPtr<ABrawlerEnemy>> Enemies;

	TArray<TWeakObjectPtr<ABrawlerEnemy>> AttackTokens;
	TWeakObjectPtr<ABrawlerFighter> LastHitEnemy;
	float LastHitEnemyTimer = 0.f;

	TArray<FEncounter> Encounters;
	TArray<FPropSpawn> Props;
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
